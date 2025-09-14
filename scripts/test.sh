#!/bin/bash

# Kali MCP Server Test Script
# This script runs comprehensive tests for the Kali MCP Server

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

# Function to run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    
    if command_exists python3; then
        python3 -m pytest tests/test_server.py -v --tb=short
        print_success "Unit tests completed"
    else
        print_error "Python3 not found"
        exit 1
    fi
}

# Function to run security tests
run_security_tests() {
    print_status "Running security tests..."
    
    if command_exists python3; then
        python3 -m pytest tests/test_security.py -v --tb=short
        print_success "Security tests completed"
    else
        print_error "Python3 not found"
        exit 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    if command_exists python3; then
        python3 -m pytest tests/test_server.py::TestIntegration -v --tb=short
        print_success "Integration tests completed"
    else
        print_error "Python3 not found"
        exit 1
    fi
}

# Function to run API tests
run_api_tests() {
    print_status "Running API tests..."
    
    # Start server in background
    print_status "Starting test server..."
    python3 server.py &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 5
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if curl -f http://localhost:5000/health >/dev/null 2>&1; then
        print_success "Health endpoint is working"
    else
        print_error "Health endpoint failed"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    
    # Test tools endpoint
    print_status "Testing tools endpoint..."
    if curl -f http://localhost:5000/tools >/dev/null 2>&1; then
        print_success "Tools endpoint is working"
    else
        print_error "Tools endpoint failed"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    
    # Test tool execution endpoint
    print_status "Testing tool execution endpoint..."
    if curl -f -X POST http://localhost:5000/run \
        -H "Content-Type: application/json" \
        -d '{"tool": "nmap", "args": "--version", "timeout": 10}' >/dev/null 2>&1; then
        print_success "Tool execution endpoint is working"
    else
        print_error "Tool execution endpoint failed"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    
    # Stop server
    kill $SERVER_PID 2>/dev/null || true
    print_success "API tests completed"
}

# Function to run Docker tests
run_docker_tests() {
    print_status "Running Docker tests..."
    
    # Build image
    print_status "Building Docker image..."
    docker build -t kali-mcp-server-test .
    
    # Test container startup
    print_status "Testing container startup..."
    docker run -d --name kali-mcp-test -p 5001:5000 kali-mcp-server-test
    
    # Wait for container to start
    sleep 10
    
    # Test health endpoint
    print_status "Testing container health endpoint..."
    if curl -f http://localhost:5001/health >/dev/null 2>&1; then
        print_success "Container health endpoint is working"
    else
        print_error "Container health endpoint failed"
        docker logs kali-mcp-test
        docker stop kali-mcp-test 2>/dev/null || true
        docker rm kali-mcp-test 2>/dev/null || true
        exit 1
    fi
    
    # Test tool execution
    print_status "Testing container tool execution..."
    if curl -f -X POST http://localhost:5001/run \
        -H "Content-Type: application/json" \
        -d '{"tool": "nmap", "args": "--version", "timeout": 10}' >/dev/null 2>&1; then
        print_success "Container tool execution is working"
    else
        print_error "Container tool execution failed"
        docker logs kali-mcp-test
        docker stop kali-mcp-test 2>/dev/null || true
        docker rm kali-mcp-test 2>/dev/null || true
        exit 1
    fi
    
    # Cleanup
    docker stop kali-mcp-test 2>/dev/null || true
    docker rm kali-mcp-test 2>/dev/null || true
    docker rmi kali-mcp-server-test 2>/dev/null || true
    
    print_success "Docker tests completed"
}

# Function to run security scan
run_security_scan() {
    print_status "Running security scan..."
    
    # Check for common security issues
    print_status "Checking for hardcoded secrets..."
    if grep -r "password\|secret\|key" --include="*.py" --include="*.yml" --include="*.yaml" . | grep -v "test" | grep -v "example" | grep -v "placeholder"; then
        print_warning "Potential hardcoded secrets found"
    else
        print_success "No hardcoded secrets found"
    fi
    
    # Check for dangerous functions
    print_status "Checking for dangerous functions..."
    if grep -r "eval\|exec\|system\|os\.system\|subprocess\.call" --include="*.py" . | grep -v "test"; then
        print_warning "Potentially dangerous functions found"
    else
        print_success "No dangerous functions found"
    fi
    
    # Check file permissions
    print_status "Checking file permissions..."
    if find . -name "*.py" -not -perm 644 | grep -q .; then
        print_warning "Some Python files have incorrect permissions"
    else
        print_success "File permissions are correct"
    fi
    
    print_success "Security scan completed"
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    # Start server in background
    print_status "Starting test server..."
    python3 server.py &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 5
    
    # Test concurrent requests
    print_status "Testing concurrent requests..."
    for i in {1..10}; do
        curl -f http://localhost:5000/health >/dev/null 2>&1 &
    done
    wait
    
    print_success "Concurrent requests test completed"
    
    # Test response times
    print_status "Testing response times..."
    start_time=$(date +%s%N)
    curl -f http://localhost:5000/health >/dev/null 2>&1
    end_time=$(date +%s%N)
    response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ $response_time -lt 1000 ]; then
        print_success "Response time is acceptable: ${response_time}ms"
    else
        print_warning "Response time is slow: ${response_time}ms"
    fi
    
    # Stop server
    kill $SERVER_PID 2>/dev/null || true
    print_success "Performance tests completed"
}

# Function to run all tests
run_all_tests() {
    print_status "Running all tests..."
    
    run_unit_tests
    run_security_tests
    run_integration_tests
    run_api_tests
    run_docker_tests
    run_security_scan
    run_performance_tests
    
    print_success "All tests completed successfully!"
}

# Function to show help
show_help() {
    echo "Kali MCP Server Test Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  unit       - Run unit tests"
    echo "  security   - Run security tests"
    echo "  integration - Run integration tests"
    echo "  api        - Run API tests"
    echo "  docker     - Run Docker tests"
    echo "  scan       - Run security scan"
    echo "  performance - Run performance tests"
    echo "  all        - Run all tests"
    echo "  help       - Show this help message"
    echo ""
}

# Main script logic
case "${1:-all}" in
    unit)
        run_unit_tests
        ;;
    security)
        run_security_tests
        ;;
    integration)
        run_integration_tests
        ;;
    api)
        run_api_tests
        ;;
    docker)
        run_docker_tests
        ;;
    scan)
        run_security_scan
        ;;
    performance)
        run_performance_tests
        ;;
    all)
        run_all_tests
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
