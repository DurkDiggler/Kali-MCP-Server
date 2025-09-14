#!/bin/bash

# Kali MCP Server Setup Script
# This script helps set up the Kali MCP Server for development or production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker installation
check_docker() {
    if command_exists docker; then
        print_success "Docker is installed"
        docker --version
    else
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Function to check Docker Compose installation
check_docker_compose() {
    if command_exists docker-compose; then
        print_success "Docker Compose is installed"
        docker-compose --version
    else
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p certs
    mkdir -p scripts
    
    print_success "Directories created"
}

# Function to generate SSL certificates for development
generate_ssl_certs() {
    print_status "Generating SSL certificates for development..."
    
    if [ ! -f "certs/cert.pem" ] || [ ! -f "certs/key.pem" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        print_success "SSL certificates generated"
    else
        print_warning "SSL certificates already exist"
    fi
}

# Function to set up environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Kali MCP Server Environment Configuration

# Server settings
ENABLE_HTTP=true
ENABLE_HTTPS=false
LOG_LEVEL=INFO
ENABLE_CORS=true

# Security settings
MAX_TIMEOUT=300
DEFAULT_TIMEOUT=60
MAX_OUTPUT_SIZE=1048576
ENABLE_SANDBOX=true
WORKING_DIRECTORY=/tmp/kali-mcp

# Additional tools (comma-separated)
EXTRA_TOOLS=gobuster,dirb,wfuzz,cewl,hashcat,crunch,medusa,ncrack,enum4linux,smbclient,rpcclient,ldapsearch,dnsutils,whois,traceroute,net-tools,iproute2

# SSL configuration (uncomment to enable HTTPS)
# ENABLE_HTTPS=true
# SSL_CERT=/opt/certs/cert.pem
# SSL_KEY=/opt/certs/key.pem
EOF
        print_success "Environment file created"
    else
        print_warning "Environment file already exists"
    fi
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    
    docker build -t kali-mcp-server .
    
    print_success "Docker image built successfully"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    if command_exists python3; then
        if [ -f "requirements.txt" ]; then
            pip3 install -r requirements.txt
        fi
        
        if [ -f "tests/test_server.py" ]; then
            python3 -m pytest tests/ -v
            print_success "Tests completed"
        else
            print_warning "Test files not found"
        fi
    else
        print_warning "Python3 not found, skipping tests"
    fi
}

# Function to start the server
start_server() {
    print_status "Starting Kali MCP Server..."
    
    docker-compose up -d
    
    print_success "Server started"
    print_status "HTTP API: http://localhost:5000"
    print_status "MCP Server: localhost:8000"
    print_status "Health Check: http://localhost:5000/health"
}

# Function to stop the server
stop_server() {
    print_status "Stopping Kali MCP Server..."
    
    docker-compose down
    
    print_success "Server stopped"
}

# Function to show server status
show_status() {
    print_status "Server Status:"
    
    if docker-compose ps | grep -q "kali-mcp-server"; then
        print_success "Server is running"
        docker-compose ps
    else
        print_warning "Server is not running"
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing server logs..."
    
    docker-compose logs -f kali-mcp-server
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    
    docker-compose down -v
    docker rmi kali-mcp-server 2>/dev/null || true
    rm -rf logs/* data/* certs/*.pem
    
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Kali MCP Server Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Initial setup (create directories, generate certs, etc.)"
    echo "  build     - Build Docker image"
    echo "  test      - Run tests"
    echo "  start     - Start the server"
    echo "  stop      - Stop the server"
    echo "  restart   - Restart the server"
    echo "  status    - Show server status"
    echo "  logs      - Show server logs"
    echo "  cleanup   - Clean up everything"
    echo "  help      - Show this help message"
    echo ""
}

# Main script logic
case "${1:-setup}" in
    setup)
        print_status "Setting up Kali MCP Server..."
        check_docker
        check_docker_compose
        create_directories
        generate_ssl_certs
        setup_env
        print_success "Setup completed successfully!"
        print_status "Run '$0 build' to build the Docker image"
        print_status "Run '$0 start' to start the server"
        ;;
    build)
        build_image
        ;;
    test)
        run_tests
        ;;
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        start_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
