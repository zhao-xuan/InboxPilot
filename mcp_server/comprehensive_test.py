#!/usr/bin/env python3
"""
Comprehensive test script for Gmail MCP Server
Tests all major functionality
"""

import asyncio
import json
from gmail_server import GmailService

async def test_gmail_comprehensive():
    """Comprehensive test of Gmail service functionality"""
    gmail = GmailService()
    
    try:
        # Test 1: Initialize the service
        print("🔑 Test 1: Initializing Gmail service...")
        await gmail.initialize()
        print("✅ Gmail service initialized successfully!")
        
        # Test 2: Get inbox messages
        print("\n📧 Test 2: Getting inbox messages...")
        messages = await gmail.get_inbox_messages(max_results=10)
        print(f"✅ Retrieved {len(messages)} messages")
        
        # Test 3: Display message details
        if messages:
            print(f"\n📩 Test 3: Latest 3 messages:")
            for i, msg in enumerate(messages[:3]):
                print(f"   {i+1}. From: {msg['from']}")
                print(f"      Subject: {msg['subject'][:60]}...")
                print(f"      Date: {msg['date']}")
                print(f"      Unread: {msg['unread']}")
                print()
        
        # Test 4: Search emails
        print("🔍 Test 4: Searching emails...")
        search_results = await gmail.search_emails("from:linkedin.com", max_results=3)
        print(f"✅ Found {len(search_results)} LinkedIn emails")
        
        # Test 5: Get unread messages
        print("\n📬 Test 5: Getting unread messages...")
        unread_messages = await gmail.get_inbox_messages(max_results=5, query="is:unread")
        print(f"✅ Found {len(unread_messages)} unread messages")
        
        # Test 6: Display service info
        print("\n📊 Test 6: Service Information:")
        print(f"   Credentials file: {gmail.credentials_file}")
        print(f"   Token file: {gmail.token_file}")
        print(f"   Service initialized: {gmail.service is not None}")
        
        print("\n🎉 All Gmail tests completed successfully!")
        
        # Summary
        print("\n📋 Test Summary:")
        print(f"   ✅ Service initialization: PASSED")
        print(f"   ✅ Inbox retrieval: PASSED ({len(messages)} messages)")
        print(f"   ✅ Email search: PASSED ({len(search_results)} results)")
        print(f"   ✅ Unread messages: PASSED ({len(unread_messages)} unread)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gmail_comprehensive()) 