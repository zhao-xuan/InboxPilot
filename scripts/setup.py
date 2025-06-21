#!/usr/bin/env python3
"""
InboxPilot Setup Script
Helps configure and test the system setup
"""

import os
import sys
import json
import asyncio
import httpx
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "MICROSOFT_TENANT_ID",
        "MICROSOFT_CLIENT_ID", 
        "MICROSOFT_CLIENT_SECRET",
        "WEBHOOK_BASE_URL",
        "LANGFLOW_WEBHOOK_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease copy env.example to .env and fill in your values.")
        return False
    
    print("✅ All required environment variables are set")
    return True

async def test_graph_api():
    """Test Microsoft Graph API connection"""
    try:
        from mcp_server.microsoft_graph_server import MicrosoftGraphClient
        
        client = MicrosoftGraphClient(
            os.getenv("MICROSOFT_TENANT_ID"),
            os.getenv("MICROSOFT_CLIENT_ID"),
            os.getenv("MICROSOFT_CLIENT_SECRET")
        )
        
        # Test authentication
        token = await client.get_access_token()
        print("✅ Microsoft Graph API authentication successful")
        
        # Test basic API call
        result = await client.make_request("GET", "/me")
        print(f"✅ Successfully connected as: {result.get('displayName', 'Unknown User')}")
        return True
        
    except Exception as e:
        print(f"❌ Microsoft Graph API test failed: {e}")
        return False

async def test_webhook_server():
    """Test webhook server health"""
    try:
        webhook_url = "http://localhost:8000/health"
        async with httpx.AsyncClient() as client:
            response = await client.get(webhook_url, timeout=5.0)
            response.raise_for_status()
            print("✅ Webhook server is running and healthy")
            return True
    except Exception as e:
        print(f"❌ Webhook server test failed: {e}")
        print("   Make sure to start the webhook server first:")
        print("   cd webhook_monitor && python email_monitor.py")
        return False

async def test_langflow_connection():
    """Test Langflow webhook connection"""
    try:
        langflow_url = os.getenv("LANGFLOW_WEBHOOK_URL")
        if not langflow_url:
            print("⚠️  LANGFLOW_WEBHOOK_URL not set, skipping test")
            return True
            
        # Try to ping Langflow
        base_url = langflow_url.split('/api/')[0]
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health", timeout=5.0)
            if response.status_code == 200:
                print("✅ Langflow server is accessible")
                return True
            else:
                print("⚠️  Langflow server responded but may not be fully ready")
                return True
    except Exception as e:
        print(f"❌ Langflow connection test failed: {e}")
        print("   Make sure Langflow is running:")
        print("   langflow run")
        return False

def create_sample_env():
    """Create a sample .env file if it doesn't exist"""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file already exists")
        return
    
    example_path = Path("env.example")
    if example_path.exists():
        import shutil
        shutil.copy(example_path, env_path)
        print("✅ Created .env file from env.example")
        print("   Please edit .env with your actual values")
    else:
        print("❌ env.example file not found")

async def setup_subscriptions():
    """Set up webhook subscriptions for testing"""
    try:
        user_email = input("Enter your email address to test subscriptions (or press Enter to skip): ").strip()
        if not user_email:
            print("⚠️  Skipping subscription setup")
            return True
        
        webhook_url = "http://localhost:8000/setup-subscriptions"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=[user_email],
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Successfully created subscriptions for {user_email}")
            print(f"   Created {len(result.get('subscriptions', []))} subscriptions")
            return True
            
    except Exception as e:
        print(f"❌ Subscription setup failed: {e}")
        return False

async def main():
    """Main setup function"""
    print("🚀 InboxPilot Setup Script")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        create_sample_env()
        print("\n❌ Setup incomplete. Please configure environment variables and try again.")
        return
    
    print("\n🔍 Testing system components...")
    
    # Test components
    tests = [
        ("Microsoft Graph API", test_graph_api),
        ("Webhook Server", test_webhook_server), 
        ("Langflow Connection", test_langflow_connection)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Setup Summary:")
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your system is ready.")
        
        # Offer to set up subscriptions
        setup_subs = input("\nWould you like to set up webhook subscriptions? (y/n): ").lower().strip()
        if setup_subs == 'y':
            await setup_subscriptions()
            
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please check the errors above.")
    
    print("\n📚 Next steps:")
    print("   1. Start Langflow: langflow run")
    print("   2. Create your AI workflow in Langflow")
    print("   3. Update LANGFLOW_WEBHOOK_URL in .env")
    print("   4. Test with real emails and Teams messages")

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, loading from system environment")
    
    asyncio.run(main()) 