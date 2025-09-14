# Kali MCP Server

A secure, production-ready Model Context Protocol (MCP) server that exposes Kali Linux security tools for use with Large Language Models (LLMs). This server provides both MCP and HTTP API interfaces, allowing LLMs to leverage powerful security tools in a controlled, sandboxed environment.

## 🚀 Features

### Core Functionality
- **Dual Interface**: Both MCP and HTTP API support
- **Tool Management**: Dynamic tool discovery and metadata
- **Security First**: Comprehensive input validation and sandboxing
- **Async Support**: High-performance async/await implementation
- **Production Ready**: Docker, monitoring, logging, and health checks

### Security Features
- **Input Sanitization**: Prevents command injection and path traversal
- **Tool Whitelisting**: Only approved tools can be executed
- **Sandboxed Execution**: Isolated environment for tool execution
- **Resource Limits**: Timeout and output size restrictions
- **Audit Logging**: Comprehensive security event logging

### Supported Tools
The server supports a curated set of Kali Linux security tools:

**Network Scanning & Enumeration**
- `nmap` - Network mapper
- `gobuster` - Directory/file brute-forcer
- `dirb` - Web content scanner
- `wfuzz` - Web application fuzzer
- `nikto` - Web vulnerability scanner

**Password Attacks**
- `hydra` - Network login cracker
- `john` - Password cracker
- `hashcat` - Advanced password recovery
- `medusa` - Parallel login brute-forcer
- `ncrack` - Network authentication tool

**Web Application Testing**
- `sqlmap` - SQL injection tool
- `cewl` - Custom word list generator

**Wireless Security**
- `aircrack-ng` - Wireless security suite

**Exploitation Framework**
- `metasploit-framework` - Penetration testing platform

**System & Network Utilities**
- `enum4linux` - SMB enumeration
- `smbclient` - SMB client
- `rpcclient` - RPC client
- `ldapsearch` - LDAP search utility
- `dig` - DNS lookup utility
- `nslookup` - DNS lookup utility
- `whois` - WHOIS lookup
- `traceroute` - Network path tracer
- `ping` - Network connectivity test
- `netstat` - Network statistics
- `ss` - Socket statistics

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- Git

## 🛠️ Installation

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/kali-mcp-server.git
   cd kali-mcp-server
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Verify the installation**
   ```bash
   curl http://localhost:5000/health
   ```

### Manual Docker Build

1. **Build the Docker image**
   ```bash
   docker build -t kali-mcp-server .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name kali-mcp-server \
     -p 5000:5000 \
     -p 8000:8000 \
     -e MAX_TIMEOUT=300 \
     -e DEFAULT_TIMEOUT=60 \
     kali-mcp-server
   ```

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server**
   ```bash
   python server.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TIMEOUT` | 300 | Maximum execution timeout (seconds) |
| `DEFAULT_TIMEOUT` | 60 | Default execution timeout (seconds) |
| `MAX_OUTPUT_SIZE` | 1048576 | Maximum output size (bytes) |
| `ENABLE_HTTP` | true | Enable HTTP API |
| `ENABLE_HTTPS` | false | Enable HTTPS |
| `SSL_CERT` | null | SSL certificate path |
| `SSL_KEY` | null | SSL private key path |
| `LOG_LEVEL` | INFO | Logging level |
| `ENABLE_CORS` | true | Enable CORS |
| `WORKING_DIRECTORY` | /tmp/kali-mcp | Working directory for tools |
| `ENABLE_SANDBOX` | true | Enable sandboxing |
| `EXTRA_TOOLS` | null | Comma-separated list of additional tools |

### Configuration File

The server supports YAML configuration files. See `config.yaml` for all available options.

## 📚 API Documentation

### HTTP API Endpoints

#### Health Check
```bash
GET /health
```
Returns server health status.

#### List Available Tools
```bash
GET /tools
```
Returns a list of all available tools with metadata.

#### Get Tool Information
```bash
GET /tools/{tool_name}
```
Returns detailed information about a specific tool.

#### Execute Tool
```bash
POST /run
Content-Type: application/json

{
  "tool": "nmap",
  "args": "-sS -O 192.168.1.1",
  "timeout": 60,
  "working_dir": "/tmp/scan"
}
```

#### Get Metrics
```bash
GET /metrics
```
Returns server metrics and statistics.

### MCP Tools

#### `list_tools()`
Returns a list of available tools.

#### `get_tool_info(tool: str)`
Returns detailed information about a specific tool.

#### `run_tool(tool: str, args: str = None, timeout: int = None, working_dir: str = None)`
Executes a tool with the specified arguments.

## 🔒 Security Considerations

### Input Validation
- All tool names are validated against a whitelist
- Command arguments are sanitized to prevent injection
- File paths are sanitized to prevent directory traversal

### Sandboxing
- Tools execute in isolated environments
- Dangerous environment variables are removed
- Working directories are restricted

### Resource Limits
- Execution timeouts prevent hanging processes
- Output size limits prevent memory exhaustion
- CPU and memory limits via Docker

### Audit Logging
- All tool executions are logged
- Security events are tracked
- Failed attempts are recorded

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=server --cov-report=html

# Run security tests only
pytest tests/test_security.py -v

# Run integration tests
pytest tests/test_server.py::TestIntegration -v
```

### Test Categories
- **Unit Tests**: Individual function testing
- **Security Tests**: Security validation testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: HTTP endpoint testing

## 🚀 Deployment

### Production Deployment

1. **Enable HTTPS**
   ```bash
   # Generate SSL certificates
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   
   # Update docker-compose.yml
   - ENABLE_HTTPS=true
   - SSL_CERT=/opt/certs/cert.pem
   - SSL_KEY=/opt/certs/key.pem
   ```

2. **Use Nginx reverse proxy**
   ```bash
   docker-compose --profile production up -d
   ```

3. **Configure monitoring**
   - Set up log aggregation
   - Configure alerting
   - Monitor resource usage

### Docker Compose Profiles

- **Default**: Basic HTTP server
- **Production**: Includes Nginx reverse proxy with SSL

## 📊 Monitoring

### Health Checks
- HTTP endpoint: `GET /health`
- Docker health check configured
- Metrics endpoint: `GET /metrics`

### Logging
- Structured JSON logging
- Log rotation configured
- Security event logging

### Metrics
- Tool execution counts
- Execution times
- Error rates
- Resource usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Setup
```bash
# Clone and setup
git clone https://github.com/your-org/kali-mcp-server.git
cd kali-mcp-server

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 server.py tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/kali-mcp-server/issues)
- **Documentation**: [Wiki](https://github.com/your-org/kali-mcp-server/wiki)
- **Security**: [Security Policy](SECURITY.md)

## 🔗 Related Projects

- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [FastMCP](https://github.com/fastmcp/fastmcp)
- [Kali Linux](https://www.kali.org/)

## 📈 Roadmap

- [ ] Web UI for tool management
- [ ] Plugin system for custom tools
- [ ] Advanced monitoring dashboard
- [ ] Multi-tenant support
- [ ] Tool execution scheduling
- [ ] Result caching
- [ ] Integration with popular LLM frameworks

## 🙏 Acknowledgments

- Kali Linux team for the excellent security tools
- FastMCP team for the MCP framework
- The open-source community for inspiration and contributions

---

**⚠️ Security Warning**: This server provides access to powerful security tools. Use responsibly and ensure proper access controls are in place. Never expose this server to untrusted networks without proper authentication and authorization.