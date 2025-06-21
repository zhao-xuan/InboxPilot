#!/usr/bin/env python3
"""
Microsoft Graph MCP Server
Provides tools for interacting with Microsoft Outlook, Teams, and To Do APIs
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
import os
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MicrosoftGraphClient:
    """Client for Microsoft Graph API operations"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.access_token = None
        self.token_expires_at = None
    
    async def get_access_token(self) -> str:
        """Get OAuth 2.0 access token using client credentials flow"""
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
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Microsoft Graph API"""
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}

# Initialize the MCP server
server = Server("microsoft-graph")

# Initialize Graph client (will be set from environment variables)
graph_client = None

def init_graph_client():
    """Initialize Microsoft Graph client from environment variables"""
    global graph_client
    
    tenant_id = os.getenv("MICROSOFT_TENANT_ID")
    client_id = os.getenv("MICROSOFT_CLIENT_ID") 
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        raise ValueError("Missing required environment variables: MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET")
    
    graph_client = MicrosoftGraphClient(tenant_id, client_id, client_secret)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Microsoft Graph tools"""
    return [
        Tool(
            name="get_emails",
            description="Retrieve emails from Outlook inbox with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user"},
                    "folder": {"type": "string", "description": "Mail folder (default: inbox)", "default": "inbox"},
                    "top": {"type": "integer", "description": "Number of emails to retrieve (max 50)", "default": 10},
                    "filter": {"type": "string", "description": "OData filter expression"},
                    "search": {"type": "string", "description": "Search query"}
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="send_email",
            description="Send an email via Outlook",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user"},
                    "to_recipients": {"type": "array", "items": {"type": "string"}, "description": "List of recipient email addresses"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                    "body_type": {"type": "string", "enum": ["text", "html"], "default": "html"},
                    "cc_recipients": {"type": "array", "items": {"type": "string"}, "description": "CC recipients"},
                    "bcc_recipients": {"type": "array", "items": {"type": "string"}, "description": "BCC recipients"}
                },
                "required": ["user_id", "to_recipients", "subject", "body"]
            }
        ),
        Tool(
            name="get_teams_messages",
            description="Retrieve Teams chat messages",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user"},
                    "chat_id": {"type": "string", "description": "Specific chat ID (optional)"},
                    "top": {"type": "integer", "description": "Number of messages to retrieve", "default": 20}
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="send_teams_message",
            description="Send a message in Microsoft Teams",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "Chat ID to send message to"},
                    "message": {"type": "string", "description": "Message content"},
                    "message_type": {"type": "string", "enum": ["text", "html"], "default": "text"}
                },
                "required": ["chat_id", "message"]
            }
        ),
        Tool(
            name="search_emails",
            description="Search emails with keywords in subject and content",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user"},
                    "keywords": {"type": "string", "description": "Keywords to search for"},
                    "top": {"type": "integer", "description": "Number of results to return", "default": 10}
                },
                "required": ["user_id", "keywords"]
            }
        ),
        Tool(
            name="create_todo_task",
            description="Create a task in Microsoft To Do",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user"},
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "due_date": {"type": "string", "description": "Due date in ISO format (YYYY-MM-DD)"},
                    "list_id": {"type": "string", "description": "To Do list ID (optional)"}
                },
                "required": ["user_id", "title"]
            }
        ),
        Tool(
            name="schedule_meeting",
            description="Schedule a meeting in Outlook calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user"},
                    "subject": {"type": "string", "description": "Meeting subject"},
                    "start_time": {"type": "string", "description": "Start time in ISO format"},
                    "end_time": {"type": "string", "description": "End time in ISO format"},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses"},
                    "body": {"type": "string", "description": "Meeting description"},
                    "location": {"type": "string", "description": "Meeting location"}
                },
                "required": ["user_id", "subject", "start_time", "end_time"]
            }
        ),
        Tool(
            name="get_user_chats",
            description="Get list of user's Teams chats",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user"},
                    "top": {"type": "integer", "description": "Number of chats to retrieve", "default": 20}
                },
                "required": ["user_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    if not graph_client:
        init_graph_client()
    
    try:
        if name == "get_emails":
            result = await get_emails(**arguments)
        elif name == "send_email":
            result = await send_email(**arguments)
        elif name == "get_teams_messages":
            result = await get_teams_messages(**arguments)
        elif name == "send_teams_message":
            result = await send_teams_message(**arguments)
        elif name == "search_emails":
            result = await search_emails(**arguments)
        elif name == "create_todo_task":
            result = await create_todo_task(**arguments)
        elif name == "schedule_meeting":
            result = await schedule_meeting(**arguments)
        elif name == "get_user_chats":
            result = await get_user_chats(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_emails(user_id: str, folder: str = "inbox", top: int = 10, filter: str = None, search: str = None) -> Dict[str, Any]:
    """Retrieve emails from Outlook"""
    endpoint = f"/users/{user_id}/mailFolders/{folder}/messages"
    
    params = {"$top": min(top, 50)}
    if filter:
        params["$filter"] = filter
    if search:
        params["$search"] = f'"{search}"'
    
    params["$select"] = "id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments"
    params["$orderby"] = "receivedDateTime desc"
    
    result = await graph_client.make_request("GET", endpoint, params=params)
    return result

async def send_email(user_id: str, to_recipients: List[str], subject: str, body: str, 
                    body_type: str = "html", cc_recipients: List[str] = None, 
                    bcc_recipients: List[str] = None) -> Dict[str, Any]:
    """Send an email via Outlook"""
    endpoint = f"/users/{user_id}/sendMail"
    
    message_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": body_type,
                "content": body
            },
            "toRecipients": [{"emailAddress": {"address": email}} for email in to_recipients]
        }
    }
    
    if cc_recipients:
        message_data["message"]["ccRecipients"] = [{"emailAddress": {"address": email}} for email in cc_recipients]
    
    if bcc_recipients:
        message_data["message"]["bccRecipients"] = [{"emailAddress": {"address": email}} for email in bcc_recipients]
    
    await graph_client.make_request("POST", endpoint, json=message_data)
    return {"status": "Email sent successfully"}

async def get_teams_messages(user_id: str, chat_id: str = None, top: int = 20) -> Dict[str, Any]:
    """Retrieve Teams chat messages"""
    if chat_id:
        endpoint = f"/chats/{chat_id}/messages"
    else:
        # Get all chats first, then messages from recent chats
        chats_endpoint = f"/users/{user_id}/chats"
        chats_result = await graph_client.make_request("GET", chats_endpoint, params={"$top": 5})
        
        all_messages = []
        for chat in chats_result.get("value", []):
            chat_messages_endpoint = f"/chats/{chat['id']}/messages"
            messages_result = await graph_client.make_request("GET", chat_messages_endpoint, params={"$top": 5})
            all_messages.extend(messages_result.get("value", []))
        
        return {"value": all_messages[:top]}
    
    params = {"$top": min(top, 50), "$orderby": "createdDateTime desc"}
    result = await graph_client.make_request("GET", endpoint, params=params)
    return result

async def send_teams_message(chat_id: str, message: str, message_type: str = "text") -> Dict[str, Any]:
    """Send a message in Microsoft Teams"""
    endpoint = f"/chats/{chat_id}/messages"
    
    message_data = {
        "body": {
            "contentType": message_type,
            "content": message
        }
    }
    
    result = await graph_client.make_request("POST", endpoint, json=message_data)
    return result

async def search_emails(user_id: str, keywords: str, top: int = 10) -> Dict[str, Any]:
    """Search emails with keywords"""
    endpoint = f"/users/{user_id}/messages"
    
    params = {
        "$search": f'"{keywords}"',
        "$top": min(top, 50),
        "$select": "id,subject,from,receivedDateTime,bodyPreview,isRead",
        "$orderby": "receivedDateTime desc"
    }
    
    result = await graph_client.make_request("GET", endpoint, params=params)
    return result

async def create_todo_task(user_id: str, title: str, description: str = None, 
                          due_date: str = None, list_id: str = None) -> Dict[str, Any]:
    """Create a task in Microsoft To Do"""
    if not list_id:
        # Get default task list
        lists_endpoint = f"/users/{user_id}/todo/lists"
        lists_result = await graph_client.make_request("GET", lists_endpoint)
        default_list = next((lst for lst in lists_result.get("value", []) if lst.get("wellknownListName") == "defaultList"), None)
        if default_list:
            list_id = default_list["id"]
        else:
            raise ValueError("No default task list found")
    
    endpoint = f"/users/{user_id}/todo/lists/{list_id}/tasks"
    
    task_data = {"title": title}
    
    if description:
        task_data["body"] = {"content": description, "contentType": "text"}
    
    if due_date:
        task_data["dueDateTime"] = {
            "dateTime": f"{due_date}T23:59:59",
            "timeZone": "UTC"
        }
    
    result = await graph_client.make_request("POST", endpoint, json=task_data)
    return result

async def schedule_meeting(user_id: str, subject: str, start_time: str, end_time: str,
                          attendees: List[str] = None, body: str = None, location: str = None) -> Dict[str, Any]:
    """Schedule a meeting in Outlook calendar"""
    endpoint = f"/users/{user_id}/calendar/events"
    
    event_data = {
        "subject": subject,
        "start": {
            "dateTime": start_time,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "UTC"
        }
    }
    
    if body:
        event_data["body"] = {"contentType": "html", "content": body}
    
    if location:
        event_data["location"] = {"displayName": location}
    
    if attendees:
        event_data["attendees"] = [
            {
                "emailAddress": {"address": email, "name": email},
                "type": "required"
            }
            for email in attendees
        ]
    
    result = await graph_client.make_request("POST", endpoint, json=event_data)
    return result

async def get_user_chats(user_id: str, top: int = 20) -> Dict[str, Any]:
    """Get list of user's Teams chats"""
    endpoint = f"/users/{user_id}/chats"
    
    params = {
        "$top": min(top, 50),
        "$select": "id,topic,chatType,createdDateTime,lastUpdatedDateTime",
        "$orderby": "lastUpdatedDateTime desc"
    }
    
    result = await graph_client.make_request("GET", endpoint, params=params)
    return result

async def main():
    """Run the MCP server"""
    # Initialize the Graph client
    init_graph_client()
    
    # Import the stdio transport
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 