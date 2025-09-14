#!/usr/bin/env python3
"""
Kali MCP Server Usage Examples

This script demonstrates how to use the Kali MCP Server via both HTTP API and MCP.
It shows various security tools and their usage patterns.
"""

import asyncio
import json
import time
from typing import Dict, Any

import httpx


class KaliMCPClient:
    """Client for interacting with the Kali MCP Server."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        response = await self.client.get(f"{self.base_url}/tools")
        return response.json()
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get information about a specific tool."""
        response = await self.client.get(f"{self.base_url}/tools/{tool_name}")
        return response.json()
    
    async def run_tool(self, tool: str, args: str = None, timeout: int = 60) -> Dict[str, Any]:
        """Execute a tool with arguments."""
        payload = {
            "tool": tool,
            "timeout": timeout
        }
        if args:
            payload["args"] = args
        
        response = await self.client.post(
            f"{self.base_url}/run",
            json=payload
        )
        return response.json()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get server metrics."""
        response = await self.client.get(f"{self.base_url}/metrics")
        return response.json()


async def demonstrate_network_scanning(client: KaliMCPClient):
    """Demonstrate network scanning tools."""
    print("🔍 Network Scanning Examples")
    print("=" * 50)
    
    # Nmap examples
    print("\n1. Nmap Version Check")
    result = await client.run_tool("nmap", "--version", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")
    
    print("\n2. Nmap Host Discovery (localhost)")
    result = await client.run_tool("nmap", "-sn 127.0.0.1", timeout=30)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:300]}...")
    
    # Ping example
    print("\n3. Ping Test")
    result = await client.run_tool("ping", "-c 3 8.8.8.8", timeout=15)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")
    
    # Traceroute example
    print("\n4. Traceroute Test")
    result = await client.run_tool("traceroute", "-m 5 8.8.8.8", timeout=30)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:300]}...")


async def demonstrate_web_testing(client: KaliMCPClient):
    """Demonstrate web application testing tools."""
    print("\n🌐 Web Application Testing Examples")
    print("=" * 50)
    
    # Nikto example (safe scan)
    print("\n1. Nikto Version Check")
    result = await client.run_tool("nikto", "-Version", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")
    
    # SQLMap version check
    print("\n2. SQLMap Version Check")
    result = await client.run_tool("sqlmap", "--version", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")
    
    # Gobuster version check
    print("\n3. Gobuster Version Check")
    result = await client.run_tool("gobuster", "version", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")


async def demonstrate_password_tools(client: KaliMCPClient):
    """Demonstrate password cracking tools."""
    print("\n🔐 Password Tools Examples")
    print("=" * 50)
    
    # John the Ripper version
    print("\n1. John the Ripper Version")
    result = await client.run_tool("john", "--version", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")
    
    # Hashcat version
    print("\n2. Hashcat Version")
    result = await client.run_tool("hashcat", "--version", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")
    
    # Hydra version
    print("\n3. Hydra Version")
    result = await client.run_tool("hydra", "-h", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:200]}...")


async def demonstrate_system_tools(client: KaliMCPClient):
    """Demonstrate system and network utilities."""
    print("\n🖥️ System Tools Examples")
    print("=" * 50)
    
    # Netstat
    print("\n1. Network Statistics")
    result = await client.run_tool("netstat", "-tuln", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:300]}...")
    
    # SS (socket statistics)
    print("\n2. Socket Statistics")
    result = await client.run_tool("ss", "-tuln", timeout=10)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:300]}...")
    
    # DNS lookup
    print("\n3. DNS Lookup")
    result = await client.run_tool("dig", "google.com", timeout=15)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:300]}...")
    
    # WHOIS lookup
    print("\n4. WHOIS Lookup")
    result = await client.run_tool("whois", "google.com", timeout=15)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Output: {result['output'][:300]}...")


async def demonstrate_error_handling(client: KaliMCPClient):
    """Demonstrate error handling and security features."""
    print("\n🛡️ Security and Error Handling Examples")
    print("=" * 50)
    
    # Test invalid tool
    print("\n1. Invalid Tool Test")
    try:
        result = await client.run_tool("invalid_tool", "test", timeout=5)
        print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"Error: {result.get('error', 'No error message')}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test dangerous arguments
    print("\n2. Dangerous Arguments Test")
    try:
        result = await client.run_tool("nmap", "test; rm -rf /", timeout=5)
        print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"Error: {result.get('error', 'No error message')}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test timeout
    print("\n3. Timeout Test")
    try:
        result = await client.run_tool("ping", "-c 100 8.8.8.8", timeout=2)
        print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"Error: {result.get('error', 'No error message')}")
    except Exception as e:
        print(f"Exception: {e}")


async def demonstrate_tool_management(client: KaliMCPClient):
    """Demonstrate tool management features."""
    print("\n🔧 Tool Management Examples")
    print("=" * 50)
    
    # List all tools
    print("\n1. List Available Tools")
    result = await client.list_tools()
    print(f"Total tools: {result['total']}")
    print("Available tools:")
    for tool in result['tools'][:10]:  # Show first 10 tools
        status = "✅" if tool['available'] else "❌"
        print(f"  {status} {tool['name']} - {tool.get('path', 'N/A')}")
    
    # Get specific tool info
    print("\n2. Get Tool Information (nmap)")
    try:
        result = await client.get_tool_info("nmap")
        print(f"Tool: {result['name']}")
        print(f"Path: {result['path']}")
        print(f"Available: {result['available']}")
        print(f"Version: {result.get('version', 'Unknown')}")
    except Exception as e:
        print(f"Error getting tool info: {e}")
    
    # Get server metrics
    print("\n3. Server Metrics")
    result = await client.get_metrics()
    print(f"Total tools: {result['total_tools']}")
    print(f"Available tools: {result['available_tools']}")
    print(f"Uptime: {result['uptime']:.2f} seconds")
    print(f"Max timeout: {result['config']['max_timeout']} seconds")
    print(f"Sandbox enabled: {result['config']['enable_sandbox']}")


async def main():
    """Main demonstration function."""
    print("🚀 Kali MCP Server Usage Examples")
    print("=" * 60)
    
    async with KaliMCPClient() as client:
        # Check server health
        print("\n🏥 Health Check")
        print("-" * 30)
        try:
            health = await client.health_check()
            print(f"Server Status: {health['status']}")
            print(f"Timestamp: {health['timestamp']}")
        except Exception as e:
            print(f"❌ Server is not responding: {e}")
            print("Make sure the server is running on http://localhost:5000")
            return
        
        # Run demonstrations
        await demonstrate_tool_management(client)
        await demonstrate_network_scanning(client)
        await demonstrate_web_testing(client)
        await demonstrate_password_tools(client)
        await demonstrate_system_tools(client)
        await demonstrate_error_handling(client)
        
        print("\n✅ All demonstrations completed!")
        print("\nFor more information, see the README.md file.")


if __name__ == "__main__":
    asyncio.run(main())
