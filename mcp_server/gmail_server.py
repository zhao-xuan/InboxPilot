#!/usr/bin/env python3
"""
Gmail MCP Server
================

Model Context Protocol server for Gmail operations including:
- Inbox monitoring and email reading
- Email sending and replying
- Email search and filtering
- Label management

Prerequisites:
1. Google Cloud Project with Gmail API enabled
2. OAuth 2.0 credentials downloaded as credentials.json
3. Environment variables configured
"""

import asyncio
import json
import logging
import os
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ Missing Google API dependencies!")
    print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
    exit(1)

# MCP imports
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import (
        Resource, Tool, TextContent,
        CallToolResult, ListResourcesResult, ListToolsResult,
        ReadResourceResult
    )
except ImportError:
    print("❌ Missing MCP dependencies!")
    print("Install with: pip install mcp")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailService:
    """Gmail API service wrapper"""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        self.token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    
    async def initialize(self):
        """Initialize Gmail API service with authentication"""
        try:
            # Load existing credentials
            if os.path.exists(self.token_file):
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, SCOPES
                )
            
            # If no valid credentials, run OAuth flow
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    try:
                        self.credentials.refresh(Request())
                    except Exception as e:
                        logger.error(f"Failed to refresh credentials: {e}")
                        self.credentials = None
                
                if not self.credentials:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"❌ Credentials file not found: {self.credentials_file}\n"
                            "Please download it from Google Cloud Console:\n"
                            "1. Go to https://console.cloud.google.com/\n"
                            "2. Enable Gmail API\n"
                            "3. Create OAuth 2.0 credentials\n"
                            "4. Download as credentials.json"
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("✅ Gmail service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gmail service: {e}")
            raise
    
    async def get_inbox_messages(self, max_results: int = 10, query: str = None):
        """Get messages from Gmail inbox"""
        try:
            # Build query
            search_query = "in:inbox"
            if query:
                search_query += f" {query}"
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get detailed message info
            detailed_messages = []
            for msg in messages:
                try:
                    message_detail = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Parse message
                    parsed_msg = self.parse_message(message_detail)
                    detailed_messages.append(parsed_msg)
                    
                except Exception as e:
                    logger.error(f"Error getting message {msg['id']}: {e}")
                    continue
            
            return detailed_messages
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise
    
    def parse_message(self, message: Dict):
        """Parse Gmail message format to simplified structure"""
        headers = message['payload'].get('headers', [])
        
        # Extract common headers
        header_dict = {}
        for header in headers:
            name = header['name'].lower()
            if name in ['from', 'to', 'cc', 'bcc', 'subject', 'date', 'message-id']:
                header_dict[name] = header['value']
        
        result = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'label_ids': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'from': header_dict.get('from', ''),
            'to': header_dict.get('to', ''),
            'cc': header_dict.get('cc', ''),
            'subject': header_dict.get('subject', ''),
            'date': header_dict.get('date', ''),
            'message_id': header_dict.get('message-id', ''),
            'size_estimate': message.get('sizeEstimate', 0),
            'internal_date': message.get('internalDate', ''),
            'unread': 'UNREAD' in message.get('labelIds', [])
        }
        
        # Extract body
        body = self.extract_message_body(message['payload'])
        result['body'] = body
        
        return result
    
    def extract_message_body(self, payload: Dict):
        """Extract message body from payload"""
        body = {'text': '', 'html': ''}
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body['text'] = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        body['html'] = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                if 'data' in payload['body']:
                    body['text'] = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                if 'data' in payload['body']:
                    body['html'] = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8')
        
        return body
    
    async def send_email(self, to: str, subject: str, body: str, cc: str = None, bcc: str = None):
        """Send an email via Gmail"""
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Send message
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                'message_id': send_message['id'],
                'thread_id': send_message['threadId'],
                'status': 'sent'
            }
            
        except HttpError as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    async def search_emails(self, query: str, max_results: int = 10):
        """Search emails with Gmail query syntax"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            detailed_messages = []
            for msg in messages:
                try:
                    message_detail = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata'
                    ).execute()
                    
                    parsed_msg = self.parse_message(message_detail)
                    detailed_messages.append(parsed_msg)
                    
                except Exception as e:
                    logger.error(f"Error getting search result {msg['id']}: {e}")
                    continue
            
            return detailed_messages
            
        except HttpError as e:
            logger.error(f"Gmail search error: {e}")
            raise

class GmailMCPServer:
    """Gmail MCP Server"""
    
    def __init__(self):
        self.server = Server("gmail-mcp-server")
        self.gmail = GmailService()
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available Gmail tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="get_inbox_messages",
                        description="Get recent messages from Gmail inbox",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of messages to retrieve (default: 10)",
                                    "default": 10
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Search query to filter messages (optional)"
                                }
                            }
                        }
                    ),
                    Tool(
                        name="send_email",
                        description="Send an email via Gmail",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "to": {
                                    "type": "string",
                                    "description": "Recipient email address"
                                },
                                "subject": {
                                    "type": "string",
                                    "description": "Email subject"
                                },
                                "body": {
                                    "type": "string",
                                    "description": "Email body content"
                                },
                                "cc": {
                                    "type": "string",
                                    "description": "CC recipients (optional)"
                                },
                                "bcc": {
                                    "type": "string",
                                    "description": "BCC recipients (optional)"
                                }
                            },
                            "required": ["to", "subject", "body"]
                        }
                    ),
                    Tool(
                        name="search_emails",
                        description="Search Gmail messages with query",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Gmail search query (e.g., 'from:sender@example.com is:unread')"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results (default: 10)",
                                    "default": 10
                                }
                            },
                            "required": ["query"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            if not self.gmail.service:
                await self.gmail.initialize()
            
            try:
                if name == "get_inbox_messages":
                    result = await self.gmail.get_inbox_messages(
                        max_results=arguments.get("max_results", 10),
                        query=arguments.get("query")
                    )
                elif name == "send_email":
                    result = await self.gmail.send_email(
                        to=arguments["to"],
                        subject=arguments["subject"],
                        body=arguments["body"],
                        cc=arguments.get("cc"),
                        bcc=arguments.get("bcc")
                    )
                elif name == "search_emails":
                    result = await self.gmail.search_emails(
                        query=arguments["query"],
                        max_results=arguments.get("max_results", 10)
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps(result, indent=2, default=str)
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: {str(e)}"
                        )
                    ],
                    isError=True
                )

# Global server instance
mcp_server = GmailMCPServer()

async def main():
    """Main function to run the Gmail MCP server"""
    mcp_server.setup_handlers()
    
    # Initialize Gmail service
    await mcp_server.gmail.initialize()
    
    # Run server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gmail-mcp-server",
                server_version="1.0.0",
                capabilities=mcp_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    print("🚀 Starting Gmail MCP Server...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Gmail MCP Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1) 