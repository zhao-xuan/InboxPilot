#!/usr/bin/env python3
"""
Enhanced Gmail MCP Server with ChromaDB Integration
Combines Gmail API access with ChromaDB vector storage for intelligent email management
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp.server import Server
    from mcp.types import Tool, Resource, TextContent
    import mcp.server.stdio
except ImportError:
    print("❌ MCP not installed. Run: pip install mcp")
    sys.exit(1)

try:
    from chromadb_setup import ChromaDBManager
except ImportError:
    print("❌ ChromaDB setup not found. Ensure chromadb_setup.py is available.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedGmailServer:
    """Enhanced Gmail MCP Server with ChromaDB integration"""
    
    def __init__(self):
        self.server = Server("enhanced-gmail-server")
        self.gmail_service = None
        self.chromadb_manager = None
        self.setup_chromadb()
        self.setup_tools()
        self.setup_resources()
    
    def setup_chromadb(self):
        """Initialize ChromaDB for email storage"""
        try:
            self.chromadb_manager = ChromaDBManager()
            self.chromadb_manager.initialize_both_instances()
            logger.info("✅ ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
    
    def setup_gmail_service(self):
        """Initialize Gmail service (with fallback if credentials missing)"""
        try:
            # Try to import Gmail dependencies
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
            creds = None
            
            # Check for existing token
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # If no valid credentials, try to get them
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists('credentials.json'):
                        logger.warning("⚠️ credentials.json not found. Gmail features will be limited.")
                        return None
                    
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail service initialized successfully")
            return self.gmail_service
            
        except ImportError:
            logger.warning("⚠️ Google API libraries not installed. Gmail features disabled.")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gmail service: {e}")
            return None
    
    def setup_tools(self):
        """Define MCP tools"""
        
        @self.server.call_tool()
        async def search_emails(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
            """Search emails using ChromaDB vector search"""
            if not self.chromadb_manager:
                return [{"error": "ChromaDB not initialized"}]
            
            try:
                # Search in ChromaDB first
                results = self.chromadb_manager.query_outlook_email(query, n_results=max_results)
                
                emails = []
                if results and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i] if results['metadatas'][0] else {}
                        emails.append({
                            "id": results['ids'][0][i] if results['ids'][0] else f"doc_{i}",
                            "content": doc,
                            "metadata": metadata,
                            "source": "chromadb"
                        })
                
                return emails
                
            except Exception as e:
                logger.error(f"Error searching emails: {e}")
                return [{"error": str(e)}]
        
        @self.server.call_tool()
        async def store_email(
            subject: str,
            sender: str, 
            content: str,
            email_type: str = "general",
            priority: str = "medium"
        ) -> Dict[str, Any]:
            """Store an email in ChromaDB"""
            if not self.chromadb_manager:
                return {"error": "ChromaDB not initialized"}
            
            try:
                # Format email content
                email_content = f"Subject: {subject}\nFrom: {sender}\n{content}"
                email_id = f"email_{datetime.now().isoformat()}_{hash(email_content) % 10000}"
                
                # Store in ChromaDB
                self.chromadb_manager.collections["outlookEmail"].add(
                    documents=[email_content],
                    ids=[email_id],
                    metadatas=[{
                        "sender": sender,
                        "subject": subject,
                        "type": email_type,
                        "priority": priority,
                        "timestamp": datetime.now().isoformat()
                    }]
                )
                
                return {
                    "success": True,
                    "email_id": email_id,
                    "message": "Email stored successfully in ChromaDB"
                }
                
            except Exception as e:
                logger.error(f"Error storing email: {e}")
                return {"error": str(e)}
        
        @self.server.call_tool()
        async def store_chat_message(
            message: str,
            user: str,
            channel: str = "general"
        ) -> Dict[str, Any]:
            """Store a Teams chat message in ChromaDB"""
            if not self.chromadb_manager:
                return {"error": "ChromaDB not initialized"}
            
            try:
                message_id = f"chat_{datetime.now().isoformat()}_{hash(message) % 10000}"
                
                # Store in ChromaDB
                self.chromadb_manager.collections["teamsChat"].add(
                    documents=[message],
                    ids=[message_id],
                    metadatas=[{
                        "user": user,
                        "channel": channel,
                        "timestamp": datetime.now().isoformat()
                    }]
                )
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "message": "Chat message stored successfully in ChromaDB"
                }
                
            except Exception as e:
                logger.error(f"Error storing chat message: {e}")
                return {"error": str(e)}
        
        @self.server.call_tool()
        async def search_chats(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
            """Search Teams chat messages using ChromaDB"""
            if not self.chromadb_manager:
                return [{"error": "ChromaDB not initialized"}]
            
            try:
                results = self.chromadb_manager.query_teams_chat(query, n_results=max_results)
                
                chats = []
                if results and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i] if results['metadatas'][0] else {}
                        chats.append({
                            "id": results['ids'][0][i] if results['ids'][0] else f"chat_{i}",
                            "message": doc,
                            "metadata": metadata,
                            "source": "chromadb"
                        })
                
                return chats
                
            except Exception as e:
                logger.error(f"Error searching chats: {e}")
                return [{"error": str(e)}]
        
        @self.server.call_tool()
        async def get_statistics() -> Dict[str, Any]:
            """Get ChromaDB instance statistics"""
            if not self.chromadb_manager:
                return {"error": "ChromaDB not initialized"}
            
            try:
                stats = self.chromadb_manager.get_stats()
                return {
                    "outlook_emails": stats.get("outlookEmail", {}).get("count", 0),
                    "teams_chats": stats.get("teamsChat", {}).get("count", 0),
                    "total_documents": sum(s.get("count", 0) for s in stats.values()),
                    "collections": list(stats.keys())
                }
            except Exception as e:
                return {"error": str(e)}
        
        @self.server.call_tool()
        async def gmail_fetch_recent(max_results: int = 10) -> List[Dict[str, Any]]:
            """Fetch recent emails from Gmail API (if available)"""
            gmail_service = self.setup_gmail_service()
            
            if not gmail_service:
                return [{"error": "Gmail service not available. Check credentials.json"}]
            
            try:
                # Fetch recent emails
                results = gmail_service.users().messages().list(
                    userId='me', 
                    maxResults=max_results
                ).execute()
                
                messages = results.get('messages', [])
                emails = []
                
                for message in messages:
                    msg = gmail_service.users().messages().get(
                        userId='me', 
                        id=message['id']
                    ).execute()
                    
                    # Extract email data
                    headers = msg['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    
                    # Get email body
                    body = ""
                    if 'parts' in msg['payload']:
                        for part in msg['payload']['parts']:
                            if part['mimeType'] == 'text/plain':
                                data = part['body']['data']
                                body = base64.urlsafe_b64decode(data).decode('utf-8')
                                break
                    elif msg['payload']['body'].get('data'):
                        body = base64.urlsafe_b64decode(
                            msg['payload']['body']['data']
                        ).decode('utf-8')
                    
                    emails.append({
                        "id": message['id'],
                        "subject": subject,
                        "sender": sender,
                        "body": body[:500] + "..." if len(body) > 500 else body,
                        "source": "gmail_api"
                    })
                
                return emails
                
            except Exception as e:
                logger.error(f"Error fetching Gmail messages: {e}")
                return [{"error": str(e)}]
    
    def setup_resources(self):
        """Define MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="chromadb://outlook-emails",
                    name="Outlook Email Collection",
                    description="ChromaDB collection containing stored emails"
                ),
                Resource(
                    uri="chromadb://teams-chats", 
                    name="Teams Chat Collection",
                    description="ChromaDB collection containing chat messages"
                ),
                Resource(
                    uri="stats://chromadb",
                    name="ChromaDB Statistics",
                    description="Statistics about stored documents"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "chromadb://outlook-emails":
                if self.chromadb_manager:
                    stats = self.chromadb_manager.get_stats()
                    count = stats.get("outlookEmail", {}).get("count", 0)
                    return f"Outlook Email Collection: {count} emails stored"
                return "ChromaDB not available"
            
            elif uri == "chromadb://teams-chats":
                if self.chromadb_manager:
                    stats = self.chromadb_manager.get_stats()
                    count = stats.get("teamsChat", {}).get("count", 0)
                    return f"Teams Chat Collection: {count} messages stored"
                return "ChromaDB not available"
            
            elif uri == "stats://chromadb":
                if self.chromadb_manager:
                    stats = self.chromadb_manager.get_stats()
                    return json.dumps(stats, indent=2)
                return "ChromaDB not available"
            
            return f"Resource not found: {uri}"

async def main():
    """Main server function"""
    print("🚀 Starting Enhanced Gmail MCP Server with ChromaDB...")
    
    server_instance = EnhancedGmailServer()
    
    # Check if Gmail credentials exist
    if not os.path.exists('credentials.json'):
        print("⚠️  Gmail credentials not found, but ChromaDB features are available!")
        print("   To enable Gmail API:")
        print("   1. Follow setup_google_credentials.md")
        print("   2. Place credentials.json in this directory")
        print("   3. Restart the server")
    
    print("✅ Server ready! Available features:")
    print("   📧 Email storage and search (ChromaDB)")
    print("   💬 Chat message storage and search (ChromaDB)")
    print("   📊 Statistics and monitoring")
    if os.path.exists('credentials.json'):
        print("   🔗 Gmail API integration")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    import base64
    asyncio.run(main()) 