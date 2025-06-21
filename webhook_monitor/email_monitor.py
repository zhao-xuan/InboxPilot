#!/usr/bin/env python3
"""
Email and Teams Message Monitor
Monitors for new emails and Teams messages using Microsoft Graph webhooks
and triggers Langflow workflows
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
import os
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
from cryptography.fernet import Fernet
import base64
import hashlib
import hmac
from urllib.parse import unquote
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Microsoft Graph Webhook Monitor")

# Environment variables
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://your-ngrok-subdomain.ngrok.io")
LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "http://localhost:7860")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY")
SUBSCRIPTION_CLIENT_STATE = os.getenv("SUBSCRIPTION_CLIENT_STATE", "InboxPilot-Secret-State")
SUBSCRIPTION_EXPIRATION_HOURS = int(os.getenv("SUBSCRIPTION_EXPIRATION_HOURS", "24"))

# Webhook paths
EMAIL_WEBHOOK_PATH = os.getenv("EMAIL_WEBHOOK_PATH", "/webhooks/email")
TEAMS_CHAT_WEBHOOK_PATH = os.getenv("TEAMS_CHAT_WEBHOOK_PATH", "/webhooks/teams/chat")
TEAMS_CHANNEL_WEBHOOK_PATH = os.getenv("TEAMS_CHANNEL_WEBHOOK_PATH", "/webhooks/teams/channel")

# Global variables for token management
access_token = None
token_expires_at = None

# Store active subscriptions
active_subscriptions: Dict[str, Dict] = {}

class GraphWebhookMonitor:
    """Monitor for Microsoft Graph webhook notifications"""
    
    def __init__(self):
        self.tenant_id = MICROSOFT_TENANT_ID
        self.client_id = MICROSOFT_CLIENT_ID
        self.client_secret = MICROSOFT_CLIENT_SECRET
        self.langflow_url = LANGFLOW_BASE_URL
        self.webhook_url = WEBHOOK_BASE_URL
        self.validation_token = SUBSCRIPTION_CLIENT_STATE
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.langflow_url]):
            raise ValueError("Missing required environment variables")
        
        self.access_token = None
        self.token_expires_at = None
        self.subscriptions = {}
    
    async def get_access_token(self) -> str:
        """Get OAuth 2.0 access token"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            return self.access_token
    
    async def make_graph_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API"""
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
    
    async def get_email_details(self, user_id: str, message_id: str) -> Dict[str, Any]:
        """Get detailed email information"""
        try:
            email = await self.make_graph_request("GET", f"/users/{user_id}/messages/{message_id}")
            return {
                "id": email.get("id"),
                "subject": email.get("subject"),
                "from": email.get("from", {}).get("emailAddress", {}),
                "to": [recipient.get("emailAddress", {}) for recipient in email.get("toRecipients", [])],
                "body": email.get("body", {}).get("content", ""),
                "bodyType": email.get("body", {}).get("contentType", ""),
                "receivedDateTime": email.get("receivedDateTime"),
                "importance": email.get("importance"),
                "hasAttachments": email.get("hasAttachments", False),
                "categories": email.get("categories", []),
                "conversationId": email.get("conversationId")
            }
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return {}
    
    async def get_teams_message_details(self, chat_id: str, message_id: str) -> Dict[str, Any]:
        """Get detailed Teams message information"""
        try:
            message = await self.make_graph_request("GET", f"/chats/{chat_id}/messages/{message_id}")
            return {
                "id": message.get("id"),
                "messageType": message.get("messageType"),
                "from": message.get("from", {}).get("user", {}),
                "body": message.get("body", {}).get("content", ""),
                "bodyType": message.get("body", {}).get("contentType", ""),
                "createdDateTime": message.get("createdDateTime"),
                "importance": message.get("importance"),
                "mentions": message.get("mentions", []),
                "reactions": message.get("reactions", []),
                "attachments": message.get("attachments", []),
                "chatId": chat_id,
                "subject": message.get("subject")
            }
        except Exception as e:
            logger.error(f"Error getting Teams message details: {e}")
            return {}
    
    async def get_teams_channel_message_details(self, team_id: str, channel_id: str, message_id: str) -> Dict[str, Any]:
        """Get detailed Teams channel message information"""
        try:
            message = await self.make_graph_request("GET", f"/teams/{team_id}/channels/{channel_id}/messages/{message_id}")
            return {
                "id": message.get("id"),
                "messageType": message.get("messageType"),
                "from": message.get("from", {}).get("user", {}),
                "body": message.get("body", {}).get("content", ""),
                "bodyType": message.get("body", {}).get("contentType", ""),
                "createdDateTime": message.get("createdDateTime"),
                "importance": message.get("importance"),
                "mentions": message.get("mentions", []),
                "reactions": message.get("reactions", []),
                "attachments": message.get("attachments", []),
                "teamId": team_id,
                "channelId": channel_id,
                "subject": message.get("subject"),
                "replyToId": message.get("replyToId")
            }
        except Exception as e:
            logger.error(f"Error getting Teams channel message details: {e}")
            return {}
    
    async def create_email_subscription(self, user_id: str) -> Dict[str, Any]:
        """Create webhook subscription for email notifications"""
        subscription_data = {
            "changeType": "created,updated",
            "notificationUrl": f"{self.webhook_url}/webhooks/email",
            "resource": f"/users/{user_id}/messages",
            "expirationDateTime": (datetime.now() + timedelta(hours=24)).isoformat() + "Z",
            "clientState": self.validation_token
        }
        
        result = await self.make_graph_request("POST", "/subscriptions", json=subscription_data)
        self.subscriptions[result["id"]] = {
            "type": "email",
            "user_id": user_id,
            "subscription_id": result["id"]
        }
        logger.info(f"Created email subscription: {result['id']}")
        return result
    
    async def create_teams_chat_subscription(self, user_id: str) -> Dict[str, Any]:
        """Create webhook subscription for Teams chat notifications"""
        subscription_data = {
            "changeType": "created",
            "notificationUrl": f"{self.webhook_url}/webhooks/teams/chat",
            "resource": f"/users/{user_id}/chats/getAllMessages",
            "expirationDateTime": (datetime.now() + timedelta(hours=24)).isoformat() + "Z",
            "clientState": self.validation_token
        }
        
        result = await self.make_graph_request("POST", "/subscriptions", json=subscription_data)
        self.subscriptions[result["id"]] = {
            "type": "teams_chat",
            "user_id": user_id,
            "subscription_id": result["id"]
        }
        logger.info(f"Created Teams chat subscription: {result['id']}")
        return result
    
    async def create_teams_channel_subscription(self, team_id: str, channel_id: str) -> Dict[str, Any]:
        """Create webhook subscription for Teams channel notifications"""
        subscription_data = {
            "changeType": "created",
            "notificationUrl": f"{self.webhook_url}/webhooks/teams/channel",
            "resource": f"/teams/{team_id}/channels/{channel_id}/messages",
            "expirationDateTime": (datetime.now() + timedelta(hours=24)).isoformat() + "Z",
            "clientState": self.validation_token
        }
        
        result = await self.make_graph_request("POST", "/subscriptions", json=subscription_data)
        self.subscriptions[result["id"]] = {
            "type": "teams_channel",
            "team_id": team_id,
            "channel_id": channel_id,
            "subscription_id": result["id"]
        }
        logger.info(f"Created Teams channel subscription: {result['id']}")
        return result
    
    async def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all teams for a user"""
        try:
            teams = await self.make_graph_request("GET", f"/users/{user_id}/joinedTeams")
            return teams.get("value", [])
        except Exception as e:
            logger.error(f"Error getting user teams: {e}")
            return []
    
    async def get_team_channels(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all channels for a team"""
        try:
            channels = await self.make_graph_request("GET", f"/teams/{team_id}/channels")
            return channels.get("value", [])
        except Exception as e:
            logger.error(f"Error getting team channels: {e}")
            return []
    
    async def renew_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Renew webhook subscription"""
        renewal_data = {
            "expirationDateTime": (datetime.now() + timedelta(hours=24)).isoformat() + "Z"
        }
        
        result = await self.make_graph_request("PATCH", f"/subscriptions/{subscription_id}", json=renewal_data)
        logger.info(f"Renewed subscription: {subscription_id}")
        return result
    
    async def delete_subscription(self, subscription_id: str):
        """Delete webhook subscription"""
        await self.make_graph_request("DELETE", f"/subscriptions/{subscription_id}")
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
        logger.info(f"Deleted subscription: {subscription_id}")
    
    async def trigger_langflow_workflow(self, data: Dict[str, Any]):
        """Trigger Langflow workflow with notification data"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.langflow_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                response.raise_for_status()
                logger.info(f"Successfully triggered Langflow workflow for {data.get('type', 'unknown')} notification")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to trigger Langflow workflow: {e}")
            raise

# Initialize the monitor
monitor = GraphWebhookMonitor()

@app.post("/webhooks/email")
async def handle_email_webhook(request: Request):
    """Handle email webhook notifications"""
    try:
        # Get the request body
        body = await request.body()
        
        # Validate the request (you should implement proper validation)
        validation_token = request.query_params.get("validationToken")
        if validation_token:
            # This is a validation request
            return JSONResponse(content=validation_token, media_type="text/plain")
        
        # Parse the notification
        notification_data = json.loads(body)
        
        for notification in notification_data.get("value", []):
            # Extract relevant information
            resource = notification.get("resource")
            change_type = notification.get("changeType")
            subscription_id = notification.get("subscriptionId")
            resource_data = notification.get("resourceData", {})
            
            logger.info(f"Received email notification: {change_type} for {resource}")
            
            # Extract user ID and message ID from resource
            user_id = None
            message_id = None
            if resource and "/users/" in resource:
                parts = resource.split("/")
                user_idx = parts.index("users") + 1
                if user_idx < len(parts):
                    user_id = parts[user_idx]
                if "/messages/" in resource:
                    msg_idx = parts.index("messages") + 1
                    if msg_idx < len(parts):
                        message_id = parts[msg_idx]
            
            # Get detailed email information
            email_details = {}
            if user_id and message_id:
                email_details = await monitor.get_email_details(user_id, message_id)
            
            # Prepare data for Langflow
            langflow_data = {
                "type": "email",
                "change_type": change_type,
                "resource": resource,
                "subscription_id": subscription_id,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "message_id": message_id,
                "email_details": email_details,
                "notification": notification
            }
            
            # Trigger Langflow workflow
            await monitor.trigger_langflow_workflow(langflow_data)
        
        return JSONResponse(content={"status": "success"})
    
    except Exception as e:
        logger.error(f"Error handling email webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/teams/chat")
async def handle_teams_chat_webhook(request: Request):
    """Handle Teams chat webhook notifications"""
    try:
        # Get the request body
        body = await request.body()
        
        # Validate the request
        validation_token = request.query_params.get("validationToken")
        if validation_token:
            # This is a validation request
            return JSONResponse(content=validation_token, media_type="text/plain")
        
        # Parse the notification
        notification_data = json.loads(body)
        
        for notification in notification_data.get("value", []):
            # Extract relevant information
            resource = notification.get("resource")
            change_type = notification.get("changeType")
            subscription_id = notification.get("subscriptionId")
            resource_data = notification.get("resourceData", {})
            
            logger.info(f"Received Teams chat notification: {change_type} for {resource}")
            
            # Extract chat ID and message ID from resource
            chat_id = None
            message_id = None
            if resource and "/chats/" in resource:
                parts = resource.split("/")
                chat_idx = parts.index("chats") + 1
                if chat_idx < len(parts):
                    chat_id = parts[chat_idx]
                if "/messages/" in resource:
                    msg_idx = parts.index("messages") + 1
                    if msg_idx < len(parts):
                        message_id = parts[msg_idx]
            
            # Get detailed message information
            message_details = {}
            if chat_id and message_id:
                message_details = await monitor.get_teams_message_details(chat_id, message_id)
            
            # Prepare data for Langflow
            langflow_data = {
                "type": "teams_chat",
                "change_type": change_type,
                "resource": resource,
                "subscription_id": subscription_id,
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id,
                "message_id": message_id,
                "message_details": message_details,
                "notification": notification
            }
            
            # Trigger Langflow workflow
            await monitor.trigger_langflow_workflow(langflow_data)
        
        return JSONResponse(content={"status": "success"})
    
    except Exception as e:
        logger.error(f"Error handling Teams chat webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/teams/channel")
async def handle_teams_channel_webhook(request: Request):
    """Handle Teams channel webhook notifications"""
    try:
        # Get the request body
        body = await request.body()
        
        # Validate the request
        validation_token = request.query_params.get("validationToken")
        if validation_token:
            # This is a validation request
            return JSONResponse(content=validation_token, media_type="text/plain")
        
        # Parse the notification
        notification_data = json.loads(body)
        
        for notification in notification_data.get("value", []):
            # Extract relevant information
            resource = notification.get("resource")
            change_type = notification.get("changeType")
            subscription_id = notification.get("subscriptionId")
            resource_data = notification.get("resourceData", {})
            
            logger.info(f"Received Teams channel notification: {change_type} for {resource}")
            
            # Extract team ID, channel ID, and message ID from resource
            team_id = None
            channel_id = None
            message_id = None
            if resource and "/teams/" in resource:
                parts = resource.split("/")
                team_idx = parts.index("teams") + 1
                if team_idx < len(parts):
                    team_id = parts[team_idx]
                if "/channels/" in resource:
                    channel_idx = parts.index("channels") + 1
                    if channel_idx < len(parts):
                        channel_id = parts[channel_idx]
                if "/messages/" in resource:
                    msg_idx = parts.index("messages") + 1
                    if msg_idx < len(parts):
                        message_id = parts[msg_idx]
            
            # Get detailed message information
            message_details = {}
            if team_id and channel_id and message_id:
                message_details = await monitor.get_teams_channel_message_details(team_id, channel_id, message_id)
            
            # Prepare data for Langflow
            langflow_data = {
                "type": "teams_channel",
                "change_type": change_type,
                "resource": resource,
                "subscription_id": subscription_id,
                "timestamp": datetime.now().isoformat(),
                "team_id": team_id,
                "channel_id": channel_id,
                "message_id": message_id,
                "message_details": message_details,
                "notification": notification
            }
            
            # Trigger Langflow workflow
            await monitor.trigger_langflow_workflow(langflow_data)
        
        return JSONResponse(content={"status": "success"})
    
    except Exception as e:
        logger.error(f"Error handling Teams channel webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/setup-subscriptions")
async def setup_subscriptions(request: Request):
    """Setup webhook subscriptions for specified users and teams"""
    try:
        body = await request.json()
        user_ids = body.get("user_ids", [])
        team_ids = body.get("team_ids", [])
        include_channels = body.get("include_channels", False)
        
        results = []
        
        # Setup user-based subscriptions
        for user_id in user_ids:
            # Create email subscription
            email_sub = await monitor.create_email_subscription(user_id)
            results.append({"type": "email", "user_id": user_id, "subscription": email_sub})
            
            # Create Teams chat subscription
            teams_chat_sub = await monitor.create_teams_chat_subscription(user_id)
            results.append({"type": "teams_chat", "user_id": user_id, "subscription": teams_chat_sub})
        
        # Setup team-based subscriptions
        if include_channels:
            for team_id in team_ids:
                channels = await monitor.get_team_channels(team_id)
                for channel in channels:
                    channel_id = channel.get("id")
                    if channel_id:
                        channel_sub = await monitor.create_teams_channel_subscription(team_id, channel_id)
                        results.append({
                            "type": "teams_channel", 
                            "team_id": team_id, 
                            "channel_id": channel_id,
                            "channel_name": channel.get("displayName"),
                            "subscription": channel_sub
                        })
        
        return JSONResponse(content={"status": "success", "subscriptions": results})
    
    except Exception as e:
        logger.error(f"Error setting up subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/teams")
async def get_user_teams(user_id: str):
    """Get all teams for a user"""
    try:
        teams = await monitor.get_user_teams(user_id)
        return JSONResponse(content={"teams": teams})
    
    except Exception as e:
        logger.error(f"Error getting user teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/channels")
async def get_team_channels(team_id: str):
    """Get all channels for a team"""
    try:
        channels = await monitor.get_team_channels(team_id)
        return JSONResponse(content={"channels": channels})
    
    except Exception as e:
        logger.error(f"Error getting team channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subscriptions")
async def list_subscriptions():
    """List all active subscriptions"""
    try:
        subscriptions = await monitor.make_graph_request("GET", "/subscriptions")
        return JSONResponse(content=subscriptions)
    
    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str):
    """Delete a specific subscription"""
    try:
        await monitor.delete_subscription(subscription_id)
        return JSONResponse(content={"status": "success", "message": f"Deleted subscription {subscription_id}"})
    
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={"status": "healthy", "timestamp": datetime.now().isoformat()})

class SubscriptionRequest(BaseModel):
    resource: str
    change_type: str = "created,updated"
    webhook_path: str
    expiration_hours: Optional[int] = None

class GraphAPIClient:
    """Microsoft Graph API client for subscription management"""
    
    def __init__(self):
        self.base_url = "https://graph.microsoft.com/v1.0"
        # Use /consumers endpoint for Microsoft personal accounts
        self.token_url = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    
    async def get_access_token(self) -> str:
        """Get access token for Microsoft Graph API"""
        global access_token, token_expires_at
        
        # Check if current token is still valid
        if access_token and token_expires_at and datetime.now() < token_expires_at:
            return access_token
        
        # Request new token
        data = {
            "client_id": MICROSOFT_CLIENT_ID,
            "client_secret": MICROSOFT_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60s buffer
            
            logger.info("Successfully obtained Microsoft Graph access token")
            return access_token
    
    async def create_subscription(self, resource: str, change_type: str, webhook_path: str, 
                                expiration_hours: Optional[int] = None) -> Dict:
        """Create a Microsoft Graph subscription"""
        token = await self.get_access_token()
        
        # Calculate expiration time
        expiration_hours = expiration_hours or SUBSCRIPTION_EXPIRATION_HOURS
        expiration_time = datetime.now() + timedelta(hours=expiration_hours)
        
        # Build notification URL
        notification_url = f"{WEBHOOK_BASE_URL.rstrip('/')}{webhook_path}"
        
        subscription_data = {
            "changeType": change_type,
            "notificationUrl": notification_url,
            "resource": resource,
            "expirationDateTime": expiration_time.isoformat() + "Z",
            "clientState": SUBSCRIPTION_CLIENT_STATE,
            "latestSupportedTlsVersion": "v1_2"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/subscriptions",
                json=subscription_data,
                headers=headers
            )
            
            if response.status_code == 201:
                subscription = response.json()
                subscription_id = subscription["id"]
                
                # Store subscription info
                active_subscriptions[subscription_id] = {
                    "id": subscription_id,
                    "resource": resource,
                    "changeType": change_type,
                    "notificationUrl": notification_url,
                    "expirationDateTime": subscription["expirationDateTime"],
                    "createdAt": datetime.now().isoformat()
                }
                
                logger.info(f"Created subscription {subscription_id} for resource: {resource}")
                return subscription
            else:
                error_msg = f"Failed to create subscription: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise HTTPException(status_code=response.status_code, detail=error_msg)
    
    async def list_subscriptions(self) -> List[Dict]:
        """List all active subscriptions"""
        token = await self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/subscriptions", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("value", [])
    
    async def renew_subscription(self, subscription_id: str, expiration_hours: Optional[int] = None) -> Dict:
        """Renew a subscription"""
        token = await self.get_access_token()
        
        expiration_hours = expiration_hours or SUBSCRIPTION_EXPIRATION_HOURS
        new_expiration = datetime.now() + timedelta(hours=expiration_hours)
        
        update_data = {
            "expirationDateTime": new_expiration.isoformat() + "Z"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/subscriptions/{subscription_id}",
                json=update_data,
                headers=headers
            )
            response.raise_for_status()
            
            subscription = response.json()
            
            # Update stored subscription info
            if subscription_id in active_subscriptions:
                active_subscriptions[subscription_id]["expirationDateTime"] = subscription["expirationDateTime"]
            
            logger.info(f"Renewed subscription {subscription_id}")
            return subscription
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription"""
        token = await self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/subscriptions/{subscription_id}", headers=headers)
            
            if response.status_code == 204:
                # Remove from stored subscriptions
                if subscription_id in active_subscriptions:
                    del active_subscriptions[subscription_id]
                
                logger.info(f"Deleted subscription {subscription_id}")
                return True
            else:
                logger.error(f"Failed to delete subscription {subscription_id}: {response.status_code}")
                return False

# Initialize Graph API client
graph_client = GraphAPIClient()

# Subscription Management Endpoints

@app.post("/subscriptions/create")
async def create_subscription(request: SubscriptionRequest):
    """Create a new Microsoft Graph subscription"""
    try:
        subscription = await graph_client.create_subscription(
            resource=request.resource,
            change_type=request.change_type,
            webhook_path=request.webhook_path,
            expiration_hours=request.expiration_hours
        )
        return {"success": True, "subscription": subscription}
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subscriptions/list")
async def list_subscriptions():
    """List all active subscriptions"""
    try:
        subscriptions = await graph_client.list_subscriptions()
        return {
            "success": True, 
            "subscriptions": subscriptions,
            "local_subscriptions": active_subscriptions
        }
    except Exception as e:
        logger.error(f"Error listing subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subscriptions/{subscription_id}/renew")
async def renew_subscription(subscription_id: str, expiration_hours: Optional[int] = None):
    """Renew a subscription"""
    try:
        subscription = await graph_client.renew_subscription(subscription_id, expiration_hours)
        return {"success": True, "subscription": subscription}
    except Exception as e:
        logger.error(f"Error renewing subscription {subscription_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str):
    """Delete a subscription"""
    try:
        success = await graph_client.delete_subscription(subscription_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deleting subscription {subscription_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subscriptions/setup-email")
async def setup_email_subscription():
    """Setup email monitoring subscription"""
    try:
        subscription = await graph_client.create_subscription(
            resource="me/mailFolders('Inbox')/messages",
            change_type="created",
            webhook_path=EMAIL_WEBHOOK_PATH
        )
        return {"success": True, "message": "Email subscription created", "subscription": subscription}
    except Exception as e:
        logger.error(f"Error setting up email subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subscriptions/setup-teams")
async def setup_teams_subscriptions():
    """Setup Teams monitoring subscriptions"""
    try:
        results = []
        
        # Create chat messages subscription
        chat_subscription = await graph_client.create_subscription(
            resource="chats/getAllMessages",
            change_type="created",
            webhook_path=TEAMS_CHAT_WEBHOOK_PATH
        )
        results.append({"type": "chat", "subscription": chat_subscription})
        
        # Create channel messages subscription
        channel_subscription = await graph_client.create_subscription(
            resource="teams/getAllMessages",
            change_type="created",
            webhook_path=TEAMS_CHANNEL_WEBHOOK_PATH
        )
        results.append({"type": "channel", "subscription": channel_subscription})
        
        return {"success": True, "message": "Teams subscriptions created", "subscriptions": results}
    except Exception as e:
        logger.error(f"Error setting up Teams subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    
    # Run the webhook server
    uvicorn.run(app, host=host, port=port) 