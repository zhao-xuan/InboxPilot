#!/usr/bin/env python3
"""
Microsoft Graph Subscription Setup Script
=========================================

This script helps you create and manage Microsoft Graph subscriptions for:
- Email monitoring (Outlook inbox)
- Teams chat messages
- Teams channel messages

Prerequisites:
1. Azure AD app registration with required permissions
2. Environment variables configured in .env file
3. Webhook server running and publicly accessible (use ngrok for local development)

Usage:
    python scripts/setup_subscriptions.py
"""

import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SubscriptionManager:
    """Manages Microsoft Graph subscriptions"""
    
    def __init__(self):
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID")
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.webhook_base_url = os.getenv("WEBHOOK_BASE_URL")
        self.client_state = os.getenv("SUBSCRIPTION_CLIENT_STATE", "InboxPilot-Secret")
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.webhook_base_url]):
            print("❌ Missing required environment variables!")
            print("Please ensure these are set in your .env file:")
            print("- MICROSOFT_TENANT_ID")
            print("- MICROSOFT_CLIENT_ID") 
            print("- MICROSOFT_CLIENT_SECRET")
            print("- WEBHOOK_BASE_URL")
            sys.exit(1)
        
        self.base_url = "https://graph.microsoft.com/v1.0"
        # Try organizational endpoint first, fall back to consumers if needed
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.consumers_token_url = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
        self.access_token = None
        self.token_expires_at = None
        self.using_consumers_endpoint = False
    
    async def get_access_token(self) -> str:
        """Get access token for Microsoft Graph API"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        print("🔑 Getting access token...")
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }
        
        # Try organizational endpoint first
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                    
                    print("✅ Successfully obtained access token (organizational)")
                    self.using_consumers_endpoint = False
                    return self.access_token
                elif response.status_code == 400 and "AADSTS9002346" in response.text:
                    # App is configured for personal accounts, try consumers endpoint
                    print("🔄 App configured for personal accounts, trying consumers endpoint...")
                    response = await client.post(self.consumers_token_url, data=data)
                    response.raise_for_status()
                    
                    token_data = response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                    
                    print("✅ Successfully obtained access token (personal accounts)")
                    self.using_consumers_endpoint = True
                    return self.access_token
                else:
                    response.raise_for_status()
                    
            except httpx.HTTPStatusError as e:
                print(f"❌ Failed to get access token: {e.response.status_code}")
                print(f"Response: {e.response.text}")
                raise
    
    async def test_webhook_endpoint(self, webhook_path: str) -> bool:
        """Test if webhook endpoint is accessible"""
        test_url = f"{self.webhook_base_url.rstrip('/')}{webhook_path}"
        
        print(f"🔍 Testing webhook endpoint: {test_url}")
        
        async with httpx.AsyncClient() as client:
            try:
                # Test with a simple GET request
                response = await client.get(test_url, timeout=10.0)
                print(f"✅ Webhook endpoint is accessible (status: {response.status_code})")
                return True
            except Exception as e:
                print(f"❌ Webhook endpoint not accessible: {str(e)}")
                print("💡 Make sure your webhook server is running and publicly accessible")
                print("   For local development, use ngrok: https://ngrok.com/")
                return False
    
    async def get_current_user_id(self) -> str:
        """Get the current user ID for user-specific endpoints"""
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Try to get user info - this might not work with app-only auth
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/me", headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    return user_data.get("id")
                else:
                    # Fallback: use a placeholder or ask user to provide
                    print("⚠️  Cannot auto-detect user ID with current authentication.")
                    print("   For personal accounts, you may need to provide a specific user ID.")
                    return None
            except Exception as e:
                print(f"⚠️  Could not get user ID: {str(e)}")
                return None
    
    async def create_subscription(self, resource: str, change_type: str, webhook_path: str, 
                                description: str, expiration_hours: int = 24) -> Optional[Dict]:
        """Create a Microsoft Graph subscription"""
        print(f"\n📝 Creating subscription for {description}...")
        print(f"   Resource: {resource}")
        print(f"   Change Type: {change_type}")
        print(f"   Webhook: {webhook_path}")
        
        # Test webhook endpoint first
        if not await self.test_webhook_endpoint(webhook_path):
            return None
        
        token = await self.get_access_token()
        
        # Calculate expiration time
        expiration_time = datetime.now() + timedelta(hours=expiration_hours)
        notification_url = f"{self.webhook_base_url.rstrip('/')}{webhook_path}"
        
        subscription_data = {
            "changeType": change_type,
            "notificationUrl": notification_url,
            "resource": resource,
            "expirationDateTime": expiration_time.isoformat() + "Z",
            "clientState": self.client_state,
            "latestSupportedTlsVersion": "v1_2"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/subscriptions",
                    json=subscription_data,
                    headers=headers
                )
                
                if response.status_code == 201:
                    subscription = response.json()
                    print(f"✅ Successfully created subscription:")
                    print(f"   ID: {subscription['id']}")
                    print(f"   Expires: {subscription['expirationDateTime']}")
                    return subscription
                else:
                    print(f"❌ Failed to create subscription: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
                    # Provide helpful error messages
                    if "delegated authentication" in response.text:
                        print("\n💡 This error occurs because:")
                        print("   - Your app is configured for personal accounts")
                        print("   - The /me endpoint requires user authentication")
                        print("   - You're using app-only authentication")
                        print("\n🔧 Solutions:")
                        print("   1. Change your Azure app to organizational accounts (recommended)")
                        print("   2. Use user-specific endpoints instead of /me")
                        print("   3. Implement delegated authentication flow")
                        print("\n📖 See docs/AZURE_APP_CONFIGURATION.md for detailed instructions")
                    
                    return None
                    
            except Exception as e:
                print(f"❌ Error creating subscription: {str(e)}")
                return None
    
    async def list_subscriptions(self) -> List[Dict]:
        """List all active subscriptions"""
        print("\n📋 Listing current subscriptions...")
        
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/subscriptions", headers=headers)
                response.raise_for_status()
                
                data = response.json()
                subscriptions = data.get("value", [])
                
                if subscriptions:
                    print(f"✅ Found {len(subscriptions)} active subscription(s):")
                    for sub in subscriptions:
                        print(f"   📌 ID: {sub['id']}")
                        print(f"      Resource: {sub['resource']}")
                        print(f"      Change Type: {sub['changeType']}")
                        print(f"      Notification URL: {sub['notificationUrl']}")
                        print(f"      Expires: {sub['expirationDateTime']}")
                        print()
                else:
                    print("ℹ️  No active subscriptions found")
                
                return subscriptions
                
            except Exception as e:
                print(f"❌ Error listing subscriptions: {str(e)}")
                return []
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription"""
        print(f"\n🗑️  Deleting subscription: {subscription_id}")
        
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(f"{self.base_url}/subscriptions/{subscription_id}", headers=headers)
                
                if response.status_code == 204:
                    print("✅ Successfully deleted subscription")
                    return True
                else:
                    print(f"❌ Failed to delete subscription: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error deleting subscription: {str(e)}")
                return False

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🚀 InboxPilot - Microsoft Graph Subscription Setup")
    print("=" * 60)
    print()

def print_menu():
    """Print main menu"""
    print("\n📋 What would you like to do?")
    print("1. 📧 Create Email Subscription (Outlook Inbox)")
    print("2. 💬 Create Teams Chat Subscription")
    print("3. 📺 Create Teams Channel Subscription")
    print("4. 🎯 Create All Subscriptions")
    print("5. 📋 List Current Subscriptions")
    print("6. 🗑️  Delete Subscription")
    print("7. ❌ Exit")
    print()

async def main():
    """Main application loop"""
    print_banner()
    
    manager = SubscriptionManager()
    
    # Test connection first
    try:
        await manager.get_access_token()
        print("✅ Successfully connected to Microsoft Graph")
        
        # Check if we can access user endpoints
        user_id = await manager.get_current_user_id()
        if not user_id:
            print("\n⚠️  CONFIGURATION ISSUE DETECTED")
            print("=" * 50)
            print("Your Azure AD app is configured for personal accounts,")
            print("but you're using application authentication.")
            print("\nThis limits what subscriptions you can create.")
            print("\n🔧 RECOMMENDED FIX:")
            print("1. Go to Azure Portal → App registrations → Your app")
            print("2. Authentication → Supported account types")
            print("3. Select: 'Accounts in this organizational directory only'")
            print("4. API permissions → Add Application permissions")
            print("5. Grant admin consent")
            print("\n📖 See docs/AZURE_APP_CONFIGURATION.md for detailed steps")
            print("=" * 50)
        else:
            print(f"✅ Detected user ID: {user_id}")
            
    except Exception as e:
        print(f"❌ Failed to connect to Microsoft Graph: {str(e)}")
        print("Please check your Azure AD app configuration and credentials.")
        return
    
    while True:
        print_menu()
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == "1":
            # Email subscription - show limitation
            print("\n⚠️  EMAIL SUBSCRIPTION LIMITATION")
            print("With your current app configuration (personal accounts),")
            print("email subscriptions using /me endpoint won't work.")
            print("\nTo fix this, you need to:")
            print("1. Change to organizational account type, OR")
            print("2. Implement delegated authentication flow")
            print("\nSee docs/AZURE_APP_CONFIGURATION.md for instructions.")
            
            proceed = input("\nTry anyway? (y/N): ").strip().lower()
            if proceed == 'y':
                await manager.create_subscription(
                    resource="me/mailFolders('Inbox')/messages",
                    change_type="created",
                    webhook_path="/webhooks/email",
                    description="Email Inbox Monitoring"
                )
        
        elif choice == "2":
            # Teams chat subscription - might work with app permissions
            print("\n💬 TEAMS CHAT SUBSCRIPTION")
            print("This requires Chat.Read.All application permission.")
            print("It may work if your app has the right permissions.")
            
            await manager.create_subscription(
                resource="chats/getAllMessages",
                change_type="created",
                webhook_path="/webhooks/teams/chat",
                description="Teams Chat Messages"
            )
        
        elif choice == "3":
            # Teams channel subscription
            print("\n📺 TEAMS CHANNEL SUBSCRIPTION")
            print("This requires ChannelMessage.Read.All application permission.")
            print("It may work if your app has the right permissions.")
            
            await manager.create_subscription(
                resource="teams/getAllMessages",
                change_type="created",
                webhook_path="/webhooks/teams/channel",
                description="Teams Channel Messages"
            )
        
        elif choice == "4":
            # Create all subscriptions with warnings
            print("\n🎯 Creating all subscriptions...")
            print("⚠️  Some may fail due to app configuration limitations.")
            
            subscriptions = [
                ("me/mailFolders('Inbox')/messages", "created", "/webhooks/email", "Email Inbox (may fail)"),
                ("chats/getAllMessages", "created", "/webhooks/teams/chat", "Teams Chat"),
                ("teams/getAllMessages", "created", "/webhooks/teams/channel", "Teams Channels")
            ]
            
            for resource, change_type, webhook_path, description in subscriptions:
                await manager.create_subscription(resource, change_type, webhook_path, description)
        
        elif choice == "5":
            # List subscriptions
            await manager.list_subscriptions()
        
        elif choice == "6":
            # Delete subscription
            subscriptions = await manager.list_subscriptions()
            if subscriptions:
                print("\n🗑️  Select subscription to delete:")
                for i, sub in enumerate(subscriptions, 1):
                    print(f"{i}. {sub['resource']} (ID: {sub['id']})")
                
                try:
                    selection = int(input("\nEnter number: ")) - 1
                    if 0 <= selection < len(subscriptions):
                        sub_id = subscriptions[selection]['id']
                        await manager.delete_subscription(sub_id)
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Please enter a valid number")
        
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}") 