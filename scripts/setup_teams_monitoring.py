#!/usr/bin/env python3
"""
Teams Monitoring Setup Script
Sets up webhook subscriptions for Teams messages via Microsoft Graph API
"""

import asyncio
import json
import os
import sys
from typing import List, Dict, Any
import httpx
from datetime import datetime

class TeamsMonitoringSetup:
    """Setup class for Teams monitoring via Microsoft Graph API"""
    
    def __init__(self):
        self.webhook_server_url = os.getenv("WEBHOOK_SERVER_URL", "http://localhost:8000")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID")
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Missing required Microsoft Graph credentials")
    
    async def setup_user_subscriptions(self, user_ids: List[str]) -> Dict[str, Any]:
        """Setup email and Teams chat subscriptions for users"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.webhook_server_url}/setup-subscriptions",
                json={
                    "user_ids": user_ids,
                    "team_ids": [],
                    "include_channels": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    async def setup_team_channel_subscriptions(self, team_ids: List[str]) -> Dict[str, Any]:
        """Setup Teams channel subscriptions for specified teams"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.webhook_server_url}/setup-subscriptions",
                json={
                    "user_ids": [],
                    "team_ids": team_ids,
                    "include_channels": True
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all teams for a user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.webhook_server_url}/users/{user_id}/teams",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("teams", [])
    
    async def get_team_channels(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all channels for a team"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.webhook_server_url}/teams/{team_id}/channels",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("channels", [])
    
    async def list_subscriptions(self) -> Dict[str, Any]:
        """List all active subscriptions"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.webhook_server_url}/subscriptions",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Delete a specific subscription"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.webhook_server_url}/subscriptions/{subscription_id}",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def check_health(self) -> bool:
        """Check if webhook server is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.webhook_server_url}/health",
                    timeout=10.0
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Webhook server health check failed: {e}")
            return False

async def main():
    """Main setup function"""
    setup = TeamsMonitoringSetup()
    
    print("🚀 Teams Monitoring Setup")
    print("=" * 50)
    
    # Check webhook server health
    print("1. Checking webhook server health...")
    if not await setup.check_health():
        print("❌ Webhook server is not running or not healthy")
        print("   Please start the webhook server first:")
        print("   cd webhook_monitor && python email_monitor.py")
        return
    print("✅ Webhook server is healthy")
    
    # Get user input
    print("\n2. Setting up Teams monitoring...")
    
    # Example user IDs (replace with actual user IDs or emails)
    user_ids = input("Enter user IDs/emails (comma-separated): ").strip().split(",")
    user_ids = [uid.strip() for uid in user_ids if uid.strip()]
    
    if not user_ids:
        print("❌ No user IDs provided")
        return
    
    try:
        # Setup user subscriptions (email + Teams chat)
        print(f"\n3. Setting up subscriptions for {len(user_ids)} users...")
        user_result = await setup.setup_user_subscriptions(user_ids)
        print("✅ User subscriptions created:")
        for sub in user_result.get("subscriptions", []):
            print(f"   - {sub['type']}: {sub.get('user_id', 'N/A')}")
        
        # Get user teams and setup channel subscriptions
        print("\n4. Discovering user teams...")
        all_team_ids = set()
        
        for user_id in user_ids:
            try:
                teams = await setup.get_user_teams(user_id)
                print(f"   User {user_id} is in {len(teams)} teams")
                for team in teams:
                    all_team_ids.add(team.get("id"))
                    print(f"     - {team.get('displayName', 'Unknown')} ({team.get('id')})")
            except Exception as e:
                print(f"   ⚠️  Could not get teams for {user_id}: {e}")
        
        # Setup team channel subscriptions
        if all_team_ids:
            setup_channels = input(f"\nSetup channel subscriptions for {len(all_team_ids)} teams? (y/N): ").lower().startswith('y')
            
            if setup_channels:
                print(f"\n5. Setting up channel subscriptions for {len(all_team_ids)} teams...")
                team_result = await setup.setup_team_channel_subscriptions(list(all_team_ids))
                print("✅ Team channel subscriptions created:")
                for sub in team_result.get("subscriptions", []):
                    print(f"   - {sub['type']}: {sub.get('team_id', 'N/A')} / {sub.get('channel_name', 'Unknown')}")
        
        # List all subscriptions
        print("\n6. Current active subscriptions:")
        subscriptions = await setup.list_subscriptions()
        for sub in subscriptions.get("value", []):
            print(f"   - {sub.get('id')}: {sub.get('resource')} ({sub.get('changeType')})")
        
        print(f"\n✅ Teams monitoring setup complete!")
        print(f"   Total subscriptions: {len(subscriptions.get('value', []))}")
        print(f"   Webhook endpoints:")
        print(f"     - Email: {setup.webhook_server_url}/webhooks/email")
        print(f"     - Teams Chat: {setup.webhook_server_url}/webhooks/teams/chat")
        print(f"     - Teams Channel: {setup.webhook_server_url}/webhooks/teams/channel")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure your Microsoft Graph app has the required permissions:")
        print("   - Mail.Read, Mail.ReadWrite")
        print("   - Chat.Read.All, Chat.ReadWrite.All")
        print("   - ChannelMessage.Read.All")
        print("   - Team.ReadBasic.All")
        print("2. Ensure admin consent has been granted")
        print("3. Check your environment variables are set correctly")

if __name__ == "__main__":
    asyncio.run(main()) 