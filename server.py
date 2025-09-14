"""MCP server exposing common Kali tools with HTTP/HTTPS access.

This module allows an LLM to invoke a curated set of Kali utilities either via
the Model Context Protocol (MCP) or through a lightweight HTTP API.  A small
amount of functionality is included to make the integration friendlier for
programmatic clients:

* The list of supported tools can be queried.
* Each invocation can specify a timeout to avoid hanging processes.
* Basic input validation ensures only approved binaries are executed.
* Comprehensive security controls and sandboxing.
* Structured logging and monitoring.
"""

import asyncio
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from fastmcp import MCP

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/opt/kali-mcp-server.log')
    ]
)
logger = logging.getLogger(__name__)

# MCP server instance
mcp = MCP("kali-mcp-server", version="1.0.0")

# Configuration
@dataclass
class Config:
    """Configuration for the Kali MCP server."""
    max_timeout: int = 300  # 5 minutes max
    default_timeout: int = 60
    max_output_size: int = 1024 * 1024  # 1MB max output
    allowed_tools: List[str] = None
    enable_http: bool = True
    enable_https: bool = False
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    log_level: str = "INFO"
    enable_cors: bool = True
    cors_origins: List[str] = None
    working_directory: str = "/tmp/kali-mcp"
    enable_sandbox: bool = True
    
    def __post_init__(self):
        if self.allowed_tools is None:
            self.allowed_tools = [
                "nmap", "sqlmap", "hydra", "john", "nikto", 
                "aircrack-ng", "metasploit-framework", "gobuster",
                "dirb", "wfuzz", "cewl", "hashcat", "crunch",
                "medusa", "ncrack", "enum4linux", "smbclient",
                "rpcclient", "ldapsearch", "dig", "nslookup",
                "whois", "traceroute", "ping", "netstat", "ss"
            ]
        
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        
        # Add extra tools from environment
        if extra := os.environ.get("EXTRA_TOOLS"):
            extra_tools = [t.strip() for t in extra.split(",") if t.strip()]
            self.allowed_tools.extend(extra_tools)
            self.allowed_tools = sorted(set(self.allowed_tools))

# Load configuration
config = Config()
config.max_timeout = int(os.environ.get("MAX_TIMEOUT", config.max_timeout))
config.default_timeout = int(os.environ.get("DEFAULT_TIMEOUT", config.default_timeout))
config.max_output_size = int(os.environ.get("MAX_OUTPUT_SIZE", config.max_output_size))
config.enable_http = os.environ.get("ENABLE_HTTP", "true").lower() == "true"
config.enable_https = os.environ.get("ENABLE_HTTPS", "false").lower() == "true"
config.ssl_cert = os.environ.get("SSL_CERT")
config.ssl_key = os.environ.get("SSL_KEY")
config.log_level = os.environ.get("LOG_LEVEL", config.log_level)
config.enable_cors = os.environ.get("ENABLE_CORS", "true").lower() == "true"
config.working_directory = os.environ.get("WORKING_DIRECTORY", config.working_directory)
config.enable_sandbox = os.environ.get("ENABLE_SANDBOX", "true").lower() == "true"

# Set logging level
logging.getLogger().setLevel(getattr(logging, config.log_level.upper()))

# Pydantic models for request/response validation
class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    tool: str = Field(..., description="Name of the tool to execute")
    args: Optional[str] = Field(None, description="Command line arguments")
    timeout: Optional[int] = Field(None, ge=1, le=config.max_timeout, description="Timeout in seconds")
    working_dir: Optional[str] = Field(None, description="Working directory for execution")
    
    @validator('tool')
    def validate_tool(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Tool name contains invalid characters')
        return v
    
    @validator('args')
    def validate_args(cls, v):
        if v is not None:
            # Basic validation to prevent command injection
            if any(char in v for char in [';', '&', '|', '`', '$', '(', ')', '<', '>']):
                raise ValueError('Arguments contain potentially dangerous characters')
        return v

class ToolExecutionResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float
    tool: str
    args: Optional[str] = None
    return_code: int

class ToolInfo(BaseModel):
    """Information about an available tool."""
    name: str
    path: str
    version: Optional[str] = None
    description: Optional[str] = None
    available: bool = True

class ToolListResponse(BaseModel):
    """Response model for tool listing."""
    tools: List[ToolInfo]
    total: int

# Security utilities
class SecurityError(Exception):
    """Security-related error."""
    pass

def sanitize_path(path: str) -> str:
    """Sanitize a file path to prevent directory traversal."""
    if not path:
        return ""
    
    # Remove any path traversal attempts
    path = path.replace("..", "").replace("//", "/")
    
    # Ensure it's within allowed directories
    if not path.startswith("/"):
        path = "/" + path
    
    return os.path.normpath(path)

def validate_tool_access(tool: str) -> bool:
    """Validate that a tool is allowed to be executed."""
    if tool not in config.allowed_tools:
        return False
    
    # Check if tool exists and is executable
    tool_path = shutil.which(tool)
    if not tool_path:
        return False
    
    # Additional security checks
    if not os.access(tool_path, os.X_OK):
        return False
    
    return True

def create_sandbox_environment(working_dir: str) -> Dict[str, str]:
    """Create a sandboxed environment for tool execution."""
    env = os.environ.copy()
    
    # Restrict environment variables
    restricted_vars = [
        'PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'LANG', 'LC_ALL'
    ]
    
    sandbox_env = {}
    for var in restricted_vars:
        if var in env:
            sandbox_env[var] = env[var]
    
    # Set working directory
    sandbox_env['PWD'] = working_dir
    
    # Disable dangerous features
    sandbox_env['LD_PRELOAD'] = ''
    sandbox_env['LD_LIBRARY_PATH'] = ''
    
    return sandbox_env

# Tool management
class ToolManager:
    """Manages available tools and their metadata."""
    
    def __init__(self):
        self._tools_cache = {}
        self._last_scan = 0
        self._scan_interval = 60  # Rescan every minute
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """Get information about a specific tool."""
        if not validate_tool_access(tool_name):
            return None
        
        tool_path = shutil.which(tool_name)
        if not tool_path:
            return None
        
        # Try to get version info
        version = None
        try:
            result = subprocess.run(
                [tool_name, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return ToolInfo(
            name=tool_name,
            path=tool_path,
            version=version,
            available=True
        )
    
    def list_tools(self) -> List[ToolInfo]:
        """List all available tools with their information."""
        tools = []
        for tool_name in config.allowed_tools:
            tool_info = self.get_tool_info(tool_name)
            if tool_info:
                tools.append(tool_info)
            else:
                tools.append(ToolInfo(
                    name=tool_name,
                    path="",
                    available=False
                ))
        
        return tools

tool_manager = ToolManager()

# MCP Tools
@mcp.tool()
def list_tools() -> List[str]:
    """Return the list of tools that may be executed."""
    return [tool.name for tool in tool_manager.list_tools() if tool.available]

@mcp.tool()
def get_tool_info(tool: str) -> Dict[str, Any]:
    """Get detailed information about a specific tool."""
    tool_info = tool_manager.get_tool_info(tool)
    if not tool_info:
        raise ValueError(f"Tool {tool!r} is not available")
    return asdict(tool_info)

@mcp.tool()
def run_tool(
    tool: str, 
    args: Optional[str] = None, 
    timeout: Optional[int] = None,
    working_dir: Optional[str] = None
) -> str:
    """Run a security tool with optional arguments.

    Parameters
    ----------
    tool:
        Name of the binary to execute. Must be present in allowed tools.
    args:
        Command-line arguments to pass. They are split with shlex.
    timeout:
        Optional timeout (in seconds) before the subprocess is aborted.
    working_dir:
        Working directory for execution.
    """
    if not validate_tool_access(tool):
        raise SecurityError(f"Tool {tool!r} is not allowed or not available")
    
    if timeout is None:
        timeout = config.default_timeout
    elif timeout > config.max_timeout:
        raise ValueError(f"Timeout {timeout} exceeds maximum allowed {config.max_timeout}")
    
    # Prepare working directory
    if working_dir:
        working_dir = sanitize_path(working_dir)
        if not os.path.exists(working_dir):
            os.makedirs(working_dir, exist_ok=True)
    else:
        working_dir = config.working_directory
        os.makedirs(working_dir, exist_ok=True)
    
    # Build command
    cmd = [tool]
    if args:
        try:
            cmd += shlex.split(args)
        except ValueError as e:
            raise ValueError(f"Invalid arguments: {e}")
    
    # Create sandboxed environment
    env = create_sandbox_environment(working_dir)
    
    logger.info(f"Executing tool: {tool} with args: {args}")
    
    start_time = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=working_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        # Check output size
        output = proc.stdout + proc.stderr
        if len(output) > config.max_output_size:
            output = output[:config.max_output_size] + "\n... (output truncated)"
            logger.warning(f"Output truncated for tool {tool} (size: {len(output)})")
        
        logger.info(f"Tool {tool} completed in {execution_time:.2f}s with return code {proc.returncode}")
        
        return output
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        logger.warning(f"Tool {tool} timed out after {execution_time:.2f}s")
        raise TimeoutError(f"Tool {tool} timed out after {timeout} seconds")
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error executing tool {tool}: {e}")
        raise

# FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Kali MCP Server")
    
    # Create working directory
    os.makedirs(config.working_directory, exist_ok=True)
    
    # Start MCP server in background
    if hasattr(mcp, 'run'):
        mcp_thread = threading.Thread(target=mcp.run, daemon=True)
        mcp_thread.start()
        logger.info("MCP server started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kali MCP Server")

app = FastAPI(
    title="Kali MCP Server",
    description="Model Context Protocol server for Kali Linux security tools",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
if config.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "Kali MCP Server",
        "version": "1.0.0",
        "status": "running",
        "mcp_port": "8000",
        "http_port": "5000"
    }

@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": str(time.time())}

@app.get("/tools", response_model=ToolListResponse)
async def list_tools_http():
    """List all available tools via HTTP."""
    tools = tool_manager.list_tools()
    return ToolListResponse(tools=tools, total=len(tools))

@app.get("/tools/{tool_name}", response_model=ToolInfo)
async def get_tool_info_http(tool_name: str):
    """Get information about a specific tool."""
    tool_info = tool_manager.get_tool_info(tool_name)
    if not tool_info:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    return tool_info

@app.post("/run", response_model=ToolExecutionResponse)
async def run_tool_http(request: ToolExecutionRequest):
    """Execute a tool via HTTP."""
    try:
        start_time = time.time()
        
        # Execute the tool
        output = run_tool(
            tool=request.tool,
            args=request.args,
            timeout=request.timeout,
            working_dir=request.working_dir
        )
        
        execution_time = time.time() - start_time
        
        return ToolExecutionResponse(
            success=True,
            output=output,
            execution_time=execution_time,
            tool=request.tool,
            args=request.args,
            return_code=0
        )
        
    except SecurityError as e:
        logger.warning(f"Security error: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        logger.warning(f"Timeout error: {e}")
        raise HTTPException(status_code=408, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/metrics")
async def get_metrics():
    """Get basic metrics about the server."""
    tools = tool_manager.list_tools()
    available_tools = len([t for t in tools if t.available])
    
    return {
        "total_tools": len(tools),
        "available_tools": available_tools,
        "uptime": time.time(),
        "config": {
            "max_timeout": config.max_timeout,
            "default_timeout": config.default_timeout,
            "max_output_size": config.max_output_size,
            "enable_sandbox": config.enable_sandbox
        }
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": time.time()
        }
    )

def main():
    """Run the server."""
    logger.info("Starting Kali MCP Server")
    
    # Determine which server to run
    if config.enable_https and config.ssl_cert and config.ssl_key:
        ssl_context = (config.ssl_cert, config.ssl_key)
        logger.info("Starting HTTPS server")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5000,
            ssl_context=ssl_context,
            log_level=config.log_level.lower()
        )
    elif config.enable_http:
        logger.info("Starting HTTP server")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5000,
            log_level=config.log_level.lower()
        )
    else:
        logger.info("Starting MCP server only")
        if hasattr(mcp, 'run'):
            mcp.run()

if __name__ == "__main__":
    main()