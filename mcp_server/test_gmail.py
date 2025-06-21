#!/usr/bin/env python3
"""
Simple test script for Gmail MCP Server
"""

import asyncio
import json
from gmail_server import GmailService

async def test_gmail():
    """Test Gmail service functionality"""
    gmail = GmailService()
    
    try:
        # Initialize the service
        print("🔑 Initializing Gmail service...")
        await gmail.initialize()
        print("✅ Gmail service initialized successfully!")
        
        # Test getting inbox messages
        print("\n📧 Getting inbox messages...")
        messages = await gmail.get_inbox_messages(max_results=5)
        print(f"✅ Retrieved {len(messages)} messages")
        
        # Print first message details
        if messages:
            first_msg = messages[0]
            print(f"\n📩 Latest message:")
            print(f"   From: {first_msg['from']}")
            print(f"   Subject: {first_msg['subject']}")
            print(f"   Date: {first_msg['date']}")
            print(f"   Unread: {first_msg['unread']}")
        
        print("\n🎉 Gmail server test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gmail()) 