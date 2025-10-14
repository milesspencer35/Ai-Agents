"""
MCP Client Test Script
This script tests the MCP server by calling its tools.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test the MCP server functionality."""
    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )
    
    print("🚀 Starting MCP server connection...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✅ Connected to MCP server\n")
            
            # List available tools
            tools = await session.list_tools()
            print("📋 Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # Test the 'add' tool
            print("🧮 Testing 'add' tool...")
            result = await session.call_tool("add", {"a": 15, "b": 27})
            print(f"Result: {result.content[0].text}\n")
            
            # Test the 'greet' tool
            print("👋 Testing 'greet' tool...")
            result = await session.call_tool("greet", {"name": "Alice"})
            print(f"Result: {result.content[0].text}\n")
            
            print("✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())