"""Comprehensive test suite for the Kali MCP server."""

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from unittest import mock
from unittest.mock import patch, MagicMock

import pytest
import httpx
from fastapi.testclient import TestClient

# Ensure the repository root is importable
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import server
from server import app, tool_manager, config


class TestSecurity:
    """Test security-related functionality."""
    
    def test_validate_tool_access_allowed_tool(self):
        """Test that allowed tools pass validation."""
        with patch('server.shutil.which', return_value='/usr/bin/nmap'):
            with patch('os.access', return_value=True):
                assert server.validate_tool_access('nmap') is True
    
    def test_validate_tool_access_disallowed_tool(self):
        """Test that disallowed tools fail validation."""
        assert server.validate_tool_access('rm') is False
    
    def test_validate_tool_access_nonexistent_tool(self):
        """Test that nonexistent tools fail validation."""
        with patch('server.shutil.which', return_value=None):
            assert server.validate_tool_access('nonexistent') is False
    
    def test_sanitize_path_normal_path(self):
        """Test path sanitization with normal paths."""
        assert server.sanitize_path("/tmp/test") == "/tmp/test"
        assert server.sanitize_path("test") == "/test"
    
    def test_sanitize_path_traversal_attempts(self):
        """Test that path traversal attempts are blocked."""
        assert ".." not in server.sanitize_path("../../../etc/passwd")
        assert "//" not in server.sanitize_path("//etc//passwd")
    
    def test_create_sandbox_environment(self):
        """Test sandbox environment creation."""
        env = server.create_sandbox_environment("/tmp/test")
        
        # Check that dangerous variables are removed
        assert 'LD_PRELOAD' not in env or env['LD_PRELOAD'] == ''
        assert 'LD_LIBRARY_PATH' not in env or env['LD_LIBRARY_PATH'] == ''
        
        # Check that working directory is set
        assert env['PWD'] == "/tmp/test"


class TestToolManager:
    """Test tool management functionality."""
    
    def test_get_tool_info_existing_tool(self):
        """Test getting info for an existing tool."""
        with patch('server.validate_tool_access', return_value=True):
            with patch('server.shutil.which', return_value='/usr/bin/nmap'):
                with patch('server.subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "Nmap version 7.94"
                    
                    tool_info = tool_manager.get_tool_info('nmap')
                    
                    assert tool_info is not None
                    assert tool_info.name == 'nmap'
                    assert tool_info.path == '/usr/bin/nmap'
                    assert tool_info.available is True
    
    def test_get_tool_info_nonexistent_tool(self):
        """Test getting info for a nonexistent tool."""
        with patch('server.validate_tool_access', return_value=False):
            tool_info = tool_manager.get_tool_info('nonexistent')
            assert tool_info is None
    
    def test_list_tools(self):
        """Test listing all tools."""
        with patch.object(tool_manager, 'get_tool_info') as mock_get_info:
            mock_tool = server.ToolInfo(name='test', path='/usr/bin/test', available=True)
            mock_get_info.return_value = mock_tool
            
            tools = tool_manager.list_tools()
            
            assert len(tools) > 0
            assert all(isinstance(tool, server.ToolInfo) for tool in tools)


class TestMCPTools:
    """Test MCP tool functions."""
    
    def test_list_tools_mcp(self):
        """Test MCP list_tools function."""
        with patch.object(tool_manager, 'list_tools') as mock_list:
            mock_list.return_value = [
                server.ToolInfo(name='nmap', path='/usr/bin/nmap', available=True),
                server.ToolInfo(name='test', path='', available=False)
            ]
            
            tools = server.list_tools()
            
            assert 'nmap' in tools
            assert 'test' not in tools  # Not available
    
    def test_get_tool_info_mcp(self):
        """Test MCP get_tool_info function."""
        with patch.object(tool_manager, 'get_tool_info') as mock_get_info:
            mock_tool = server.ToolInfo(name='nmap', path='/usr/bin/nmap', available=True)
            mock_get_info.return_value = mock_tool
            
            result = server.get_tool_info('nmap')
            
            assert result['name'] == 'nmap'
            assert result['path'] == '/usr/bin/nmap'
            assert result['available'] is True
    
    def test_get_tool_info_mcp_nonexistent(self):
        """Test MCP get_tool_info with nonexistent tool."""
        with patch.object(tool_manager, 'get_tool_info', return_value=None):
            with pytest.raises(ValueError, match="Tool 'nonexistent' is not available"):
                server.get_tool_info('nonexistent')
    
    def test_run_tool_mcp_success(self):
        """Test successful MCP tool execution."""
        with patch('server.validate_tool_access', return_value=True):
            with patch('server.subprocess.run') as mock_run:
                mock_run.return_value.stdout = "test output"
                mock_run.return_value.stderr = ""
                mock_run.return_value.returncode = 0
                
                with patch('os.makedirs'):
                    result = server.run_tool('nmap', '-V', timeout=10)
                    
                    assert result == "test output"
                    mock_run.assert_called_once()
    
    def test_run_tool_mcp_security_error(self):
        """Test MCP tool execution with security error."""
        with patch('server.validate_tool_access', return_value=False):
            with pytest.raises(server.SecurityError, match="Tool 'rm' is not allowed"):
                server.run_tool('rm', 'test')
    
    def test_run_tool_mcp_timeout_error(self):
        """Test MCP tool execution with timeout."""
        with patch('server.validate_tool_access', return_value=True):
            with patch('server.subprocess.run') as mock_run:
                mock_run.side_effect = server.subprocess.TimeoutExpired('nmap', 10)
                
                with patch('os.makedirs'):
                    with pytest.raises(TimeoutError):
                        server.run_tool('nmap', '-V', timeout=10)


class TestHTTPAPI:
    """Test HTTP API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Kali MCP Server"
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_list_tools_endpoint(self, client):
        """Test tools listing endpoint."""
        with patch.object(tool_manager, 'list_tools') as mock_list:
            mock_list.return_value = [
                server.ToolInfo(name='nmap', path='/usr/bin/nmap', available=True)
            ]
            
            response = client.get("/tools")
            assert response.status_code == 200
            
            data = response.json()
            assert "tools" in data
            assert "total" in data
            assert len(data["tools"]) == 1
            assert data["tools"][0]["name"] == "nmap"
    
    def test_get_tool_info_endpoint(self, client):
        """Test individual tool info endpoint."""
        with patch.object(tool_manager, 'get_tool_info') as mock_get_info:
            mock_tool = server.ToolInfo(name='nmap', path='/usr/bin/nmap', available=True)
            mock_get_info.return_value = mock_tool
            
            response = client.get("/tools/nmap")
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == "nmap"
            assert data["path"] == "/usr/bin/nmap"
    
    def test_get_tool_info_endpoint_not_found(self, client):
        """Test tool info endpoint with nonexistent tool."""
        with patch.object(tool_manager, 'get_tool_info', return_value=None):
            response = client.get("/tools/nonexistent")
            assert response.status_code == 404
    
    def test_run_tool_endpoint_success(self, client):
        """Test tool execution endpoint success."""
        with patch('server.run_tool', return_value="test output") as mock_run:
            response = client.post(
                "/run",
                json={
                    "tool": "nmap",
                    "args": "-V",
                    "timeout": 10
                }
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["output"] == "test output"
            assert data["tool"] == "nmap"
            assert data["return_code"] == 0
            
            mock_run.assert_called_once_with(
                tool="nmap",
                args="-V",
                timeout=10,
                working_dir=None
            )
    
    def test_run_tool_endpoint_validation_error(self, client):
        """Test tool execution endpoint with validation error."""
        response = client.post(
            "/run",
            json={
                "tool": "nmap",
                "args": "test; rm -rf /",  # Invalid characters
                "timeout": 10
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_run_tool_endpoint_security_error(self, client):
        """Test tool execution endpoint with security error."""
        with patch('server.run_tool', side_effect=server.SecurityError("Tool not allowed")):
            response = client.post(
                "/run",
                json={
                    "tool": "rm",
                    "args": "test"
                }
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "Tool not allowed" in data["error"]
    
    def test_run_tool_endpoint_timeout_error(self, client):
        """Test tool execution endpoint with timeout error."""
        with patch('server.run_tool', side_effect=TimeoutError("Tool timed out")):
            response = client.post(
                "/run",
                json={
                    "tool": "nmap",
                    "args": "-V",
                    "timeout": 1
                }
            )
            
            assert response.status_code == 408
            data = response.json()
            assert "timed out" in data["error"]
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        with patch.object(tool_manager, 'list_tools') as mock_list:
            mock_list.return_value = [
                server.ToolInfo(name='nmap', path='/usr/bin/nmap', available=True),
                server.ToolInfo(name='test', path='', available=False)
            ]
            
            response = client.get("/metrics")
            assert response.status_code == 200
            
            data = response.json()
            assert "total_tools" in data
            assert "available_tools" in data
            assert "uptime" in data
            assert "config" in data


class TestConfiguration:
    """Test configuration management."""
    
    def test_config_defaults(self):
        """Test that configuration has sensible defaults."""
        assert config.max_timeout > 0
        assert config.default_timeout > 0
        assert config.max_output_size > 0
        assert len(config.allowed_tools) > 0
        assert config.working_directory is not None
    
    def test_config_environment_override(self):
        """Test that environment variables override config."""
        with patch.dict(os.environ, {'MAX_TIMEOUT': '600'}):
            # Reimport to pick up new environment
            import importlib
            importlib.reload(server)
            assert server.config.max_timeout == 600


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test a complete workflow from HTTP request to tool execution."""
        with patch('server.validate_tool_access', return_value=True):
            with patch('server.subprocess.run') as mock_run:
                mock_run.return_value.stdout = "Nmap version 7.94"
                mock_run.return_value.stderr = ""
                mock_run.return_value.returncode = 0
                
                with patch('os.makedirs'):
                    client = TestClient(app)
                    
                    # List tools
                    response = client.get("/tools")
                    assert response.status_code == 200
                    
                    # Run a tool
                    response = client.post(
                        "/run",
                        json={
                            "tool": "nmap",
                            "args": "--version",
                            "timeout": 10
                        }
                    )
                    assert response.status_code == 200
                    
                    data = response.json()
                    assert data["success"] is True
                    assert "Nmap version" in data["output"]


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON requests."""
        client = TestClient(app)
        response = client.post(
            "/run",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        client = TestClient(app)
        response = client.post(
            "/run",
            json={"args": "-V"}  # Missing 'tool' field
        )
        assert response.status_code == 422
    
    def test_tool_execution_exception(self):
        """Test handling of unexpected exceptions during tool execution."""
        with patch('server.run_tool', side_effect=Exception("Unexpected error")):
            client = TestClient(app)
            response = client.post(
                "/run",
                json={
                    "tool": "nmap",
                    "args": "-V"
                }
            )
            assert response.status_code == 500
            data = response.json()
            assert "Internal server error" in data["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])