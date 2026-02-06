#!/usr/bin/env python3
"""
Test script for password reset user validation
Tests both the backend API and MCP tool
"""

import asyncio
import httpx
import json


# Backend API Configuration
API_BASE_URL = "http://149.102.158.71:4798"


async def test_backend_api():
    """Test the backend API endpoint directly"""
    print("=" * 60)
    print("Testing Backend API: /api/v1/auth/validate-user")
    print("=" * 60)

    test_cases = [
        {"username": "engineer", "should_exist": True},
        {"username": "manager", "should_exist": True},
        {"username": "finance", "should_exist": True},
        {"username": "admin", "should_exist": True},
        {"username": "unknown_user", "should_exist": False},
        {"username": "test123", "should_exist": False},
        {"username": " engineer ", "should_exist": True},  # Test whitespace handling
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for test in test_cases:
            username = test["username"]
            expected_exists = test["should_exist"]

            print(f"\n📝 Testing username: '{username}'")
            print(f"   Expected: {'EXISTS' if expected_exists else 'NOT FOUND'}")

            try:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/auth/validate-user",
                    json={"username": username},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    exists = data.get("exists", False)
                    message = data.get("message", "")

                    status = "✅ PASS" if exists == expected_exists else "❌ FAIL"
                    print(f"   Result: {status}")
                    print(f"   Exists: {exists}")
                    print(f"   Message: {message}")
                else:
                    print(f"   ❌ FAIL - HTTP {response.status_code}")
                    print(f"   Response: {response.text}")

            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")


async def test_mcp_tool():
    """Test the MCP tool (requires MCP server to be running)"""
    print("\n" + "=" * 60)
    print("Testing MCP Tool: validate_user_for_password_reset")
    print("=" * 60)
    print("\nNote: This requires the MCP server to be running.")
    print("Start it with: python mcp_sap.py --stdio")
    print("\nFor now, we've tested the underlying API endpoint.")
    print("The MCP tool uses the same API endpoint internally.")


async def main():
    """Run all tests"""
    print("\n🔐 SAP Password Reset User Validation - Test Suite\n")

    # Test backend API
    await test_backend_api()

    # Info about MCP tool testing
    await test_mcp_tool()

    print("\n" + "=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)

    print("\n📚 How to use the MCP tool:")
    print("   1. Start MCP server: python mcp_sap.py")
    print("   2. Connect your MCP client")
    print("   3. Call: validate_user_for_password_reset(username='engineer')")
    print("\n💡 Integration Examples:")
    print("   - Agent: 'Reset password for user engineer'")
    print("   - Agent calls: validate_user_for_password_reset('engineer')")
    print("   - Agent receives: User exists confirmation")
    print("   - Agent: Proceeds with password reset flow")


if __name__ == "__main__":
    asyncio.run(main())
