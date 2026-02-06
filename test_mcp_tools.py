#!/usr/bin/env python3
"""Simple test to verify MCP unified server tools"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    print("=" * 80)
    print("MCP UNIFIED SERVER TEST")
    print("=" * 80)

    server_params = StdioServerParameters(
        command="/home/pradeep1a/Network-apps/mcp_venv/bin/python3",
        args=["/home/pradeep1a/Network-apps/mcp_unified.py"]
    )

    print("\n1. Starting MCP server subprocess...")
    async with stdio_client(server_params) as (read, write):
        print("   ✓ Subprocess started\n")

        print("2. Creating client session...")
        async with ClientSession(read, write) as session:
            print("   ✓ Session created\n")

            print("3. Initializing session...")
            init_result = await session.initialize()
            print(f"   ✓ Initialized - Server: {init_result.serverInfo.name}")
            print(f"   Version: {init_result.serverInfo.version}\n")

            print("4. Listing available tools...")
            tools = await session.list_tools()
            print(f"   ✓ Found {len(tools.tools)} tools\n")

            print("=" * 80)
            print("AVAILABLE TOOLS")
            print("=" * 80)

            # Categorize tools
            categories = {}
            for tool in tools.tools:
                prefix = tool.name.split('_')[0]
                if prefix not in categories:
                    categories[prefix] = []
                categories[prefix].append(tool.name)

            for category in sorted(categories.keys()):
                print(f"\n{category.upper()} Tools ({len(categories[category])}):")
                for tool_name in sorted(categories[category]):
                    print(f"  • {tool_name}")

            print("\n" + "=" * 80)
            print("TESTING BASIC FUNCTIONS")
            print("=" * 80)

            # Test 1: List services
            print("\n1. Testing: list_services()")
            try:
                result = await session.call_tool("list_services", arguments={})
                data = json.loads(result.content[0].text)
                print("   ✓ Success!")
                for service, info in data.items():
                    print(f"   - {info['name']}: {info['base_url']}")
            except Exception as e:
                print(f"   ✗ Failed: {e}")

            # Test 2: Health check
            print("\n2. Testing: health_check_all()")
            try:
                result = await session.call_tool("health_check_all", arguments={})
                data = json.loads(result.content[0].text)
                print("   ✓ Success!")
                for service, status in data.items():
                    health = status.get('status', 'unknown')
                    symbol = '✓' if health == 'healthy' else '✗'
                    print(f"   {symbol} {service}: {health}")
            except Exception as e:
                print(f"   ✗ Failed: {e}")

            print("\n" + "=" * 80)
            print(f"✓ TEST COMPLETED - {len(tools.tools)} tools available!")
            print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
