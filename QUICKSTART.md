# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker and Docker Compose installed
- Git (optional, for cloning)

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/kali-mcp-server.git
cd kali-mcp-server
chmod +x scripts/setup.sh
./scripts/setup.sh setup
```

### 2. Build and Run
```bash
# Using Makefile (recommended)
make quick-start

# Or using Docker Compose directly
docker-compose up -d
```

### 3. Verify Installation
```bash
# Check health
curl http://localhost:5000/health

# List available tools
curl http://localhost:5000/tools

# Run a simple test
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{"tool": "nmap", "args": "--version", "timeout": 10}'
```

### 4. Run Examples
```bash
# Install Python dependencies
pip install httpx

# Run example script
python examples/example_usage.py
```

## 🛠️ Development Commands

```bash
# Setup development environment
make dev-setup

# Run tests
make test

# Run in development mode
make run-dev

# Format code
make format

# Run security scan
make security-scan
```

## 🐳 Docker Commands

```bash
# Build image
make docker-build

# Run container
make docker-run

# View logs
make docker-logs

# Stop container
make docker-stop

# Clean up
make docker-clean
```

## 📊 Monitoring

```bash
# Check status
make status

# View logs
make logs

# Check health
make health

# View metrics
curl http://localhost:5000/metrics
```

## 🔧 Configuration

Edit `.env` file or set environment variables:

```bash
# Basic configuration
MAX_TIMEOUT=300
DEFAULT_TIMEOUT=60
LOG_LEVEL=INFO

# Add more tools
EXTRA_TOOLS=tool1,tool2,tool3

# Enable HTTPS
ENABLE_HTTPS=true
SSL_CERT=/path/to/cert.pem
SSL_KEY=/path/to/key.pem
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-security
make test-integration
make test-api
make test-docker

# Run security scan
make security-scan
```

## 🚀 Production Deployment

```bash
# Build for production
make prod-build

# Run with Nginx proxy
make prod-run

# Stop production services
make prod-stop
```

## 📚 API Examples

### List Tools
```bash
curl http://localhost:5000/tools
```

### Get Tool Info
```bash
curl http://localhost:5000/tools/nmap
```

### Execute Tool
```bash
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "nmap",
    "args": "-sS -O 192.168.1.1",
    "timeout": 60
  }'
```

### Get Metrics
```bash
curl http://localhost:5000/metrics
```

## 🔒 Security Notes

- The server runs in a sandboxed environment
- Only whitelisted tools can be executed
- All inputs are validated and sanitized
- Resource limits prevent abuse
- All activities are logged

## 🆘 Troubleshooting

### Server Not Starting
```bash
# Check logs
make logs

# Check status
make status

# Restart
make restart
```

### Tool Not Found
```bash
# Check available tools
curl http://localhost:5000/tools

# Add tool to EXTRA_TOOLS in .env
echo "EXTRA_TOOLS=tool_name" >> .env
```

### Permission Issues
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Check Docker permissions
sudo usermod -aG docker $USER
```

## 📖 More Information

- [Full Documentation](README.md)
- [Security Policy](SECURITY.md)
- [Improvements Summary](IMPROVEMENTS.md)
- [API Documentation](http://localhost:5000/docs) (when running)

## 🤝 Support

- [GitHub Issues](https://github.com/your-org/kali-mcp-server/issues)
- [Security Issues](SECURITY.md#reporting-a-vulnerability)
- [Documentation](README.md)

---

**Ready to go!** 🎉 Your Kali MCP Server is now running and ready to use with your LLM.
