#!/usr/bin/env python3
"""
Test script for Microsoft Graph MCP Server
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the mcp_server directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_server"))

from microsoft_graph_server import MicrosoftGraphClient

async def test_mcp_tools():
    """Test MCP server tools"""
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Initialize client
    try:
        client = MicrosoftGraphClient(
            os.getenv("MICROSOFT_TENANT_ID"),
            os.getenv("MICROSOFT_CLIENT_ID"),
            os.getenv("MICROSOFT_CLIENT_SECRET")
        )
        print("✅ MCP client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        return
    
    # Test authentication
    try:
        token = await client.get_access_token()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Test basic API calls
    tests = [
        {
            "name": "Get User Profile",
            "method": "GET",
            "endpoint": "/me",
            "expected_fields": ["displayName", "mail", "id"]
        },
        {
            "name": "Get Emails",
            "method": "GET", 
            "endpoint": "/me/messages",
            "params": {"$top": 5, "$select": "subject,from,receivedDateTime"},
            "expected_fields": ["value"]
        },
        {
            "name": "Get Task Lists",
            "method": "GET",
            "endpoint": "/me/todo/lists",
            "expected_fields": ["value"]
        },
        {
            "name": "Get Teams Chats",
            "method": "GET",
            "endpoint": "/me/chats",
            "params": {"$top": 5},
            "expected_fields": ["value"]
        }
    ]
    
    for test in tests:
        try:
            print(f"\n🔍 Testing: {test['name']}")
            
            kwargs = {}
            if "params" in test:
                kwargs["params"] = test["params"]
            
            result = await client.make_request(
                test["method"],
                test["endpoint"],
                **kwargs
            )
            
            # Check expected fields
            missing_fields = []
            for field in test["expected_fields"]:
                if field not in result:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️  Missing expected fields: {missing_fields}")
            else:
                print(f"✅ {test['name']} successful")
                
                # Print some sample data
                if "value" in result and result["value"]:
                    print(f"   Found {len(result['value'])} items")
                elif "displayName" in result:
                    print(f"   User: {result['displayName']}")
                    
        except Exception as e:
            print(f"❌ {test['name']} failed: {e}")
    
    print("\n" + "=" * 50)
    print("🧪 MCP Tools Test Complete")

async def test_tool_functions():
    """Test the individual tool functions"""
    print("\n🔧 Testing MCP Tool Functions...")
    
    # Import tool functions
    from microsoft_graph_server import (
        get_emails, search_emails, get_user_chats,
        create_todo_task, graph_client, init_graph_client
    )
    
    # Initialize graph client
    init_graph_client()
    
    # Test get_emails
    try:
        print("\n🔍 Testing get_emails...")
        emails = await get_emails("me", top=3)
        if "value" in emails:
            print(f"✅ Retrieved {len(emails['value'])} emails")
            for email in emails["value"][:2]:  # Show first 2
                print(f"   - {email.get('subject', 'No Subject')}")
        else:
            print("⚠️  Unexpected email response format")
    except Exception as e:
        print(f"❌ get_emails failed: {e}")
    
    # Test search_emails
    try:
        print("\n🔍 Testing search_emails...")
        search_results = await search_emails("me", "meeting", top=3)
        if "value" in search_results:
            print(f"✅ Found {len(search_results['value'])} emails matching 'meeting'")
        else:
            print("⚠️  No search results or unexpected format")
    except Exception as e:
        print(f"❌ search_emails failed: {e}")
    
    # Test get_user_chats
    try:
        print("\n🔍 Testing get_user_chats...")
        chats = await get_user_chats("me", top=3)
        if "value" in chats:
            print(f"✅ Retrieved {len(chats['value'])} chats")
        else:
            print("⚠️  No chats found or unexpected format")
    except Exception as e:
        print(f"❌ get_user_chats failed: {e}")
    
    # Test create_todo_task (optional - will actually create a task)
    create_task = input("\n❓ Do you want to test creating a TODO task? (y/n): ").lower().strip()
    if create_task == 'y':
        try:
            print("\n🔍 Testing create_todo_task...")
            task = await create_todo_task(
                "me", 
                "Test Task from InboxPilot",
                "This is a test task created by the MCP server test script"
            )
            if "id" in task:
                print(f"✅ Created task: {task.get('title')}")
                print(f"   Task ID: {task['id']}")
            else:
                print("⚠️  Task created but unexpected response format")
        except Exception as e:
            print(f"❌ create_todo_task failed: {e}")

def main():
    """Main test function"""
    print("🧪 Microsoft Graph MCP Server Test")
    print("=" * 50)
    
    # Check environment
    required_vars = ["MICROSOFT_TENANT_ID", "MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set up your .env file first.")
        return
    
    # Run tests
    asyncio.run(test_mcp_tools())
    asyncio.run(test_tool_functions())
    
    print("\n🎯 Test Summary:")
    print("   - Basic API connectivity: Tested")
    print("   - Authentication: Tested")
    print("   - Email operations: Tested")
    print("   - Teams operations: Tested")
    print("   - TODO operations: Tested (optional)")
    print("\n✅ MCP server testing complete!")

if __name__ == "__main__":
    main() 