#!/usr/bin/env python3
"""
InboxPilot Server Startup Script
===============================

This script starts both the webhook monitor and MCP server.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def start_webhook_server():
    """Start the webhook monitor server"""
    print("🚀 Starting Webhook Monitor Server...")
    
    try:
        # Import and start the webhook server
        from webhook_monitor.email_monitor import app
        import uvicorn
        
        print("   📡 Server: http://127.0.0.1:8000")
        print("   📋 Health: http://127.0.0.1:8000/health")
        print("   📊 Docs: http://127.0.0.1:8000/docs")
        print()
        
        # Start the server
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8000, 
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ Failed to start webhook server: {e}")
        sys.exit(1)

def start_mcp_server():
    """Start the MCP server"""
    print("🚀 Starting MCP Server...")
    
    try:
        from mcp_server.microsoft_graph_server import main
        print("   🔧 MCP Server starting...")
        main()
        
    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        sys.exit(1)

def print_banner():
    """Print startup banner"""
    print("=" * 60)
    print("🚀 InboxPilot - Starting Servers")
    print("=" * 60)
    print()
    
    # Check environment variables
    required_vars = [
        "MICROSOFT_TENANT_ID",
        "MICROSOFT_CLIENT_ID", 
        "MICROSOFT_CLIENT_SECRET"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("💡 Servers will start but may not function properly.")
        print("   Update your .env file with the correct values.")
        print()
    else:
        print("✅ Environment variables configured")
        print()

def main():
    """Main function"""
    print_banner()
    
    # For now, just start the webhook server
    # In a real deployment, you'd want to start both servers in separate processes
    print("Starting Webhook Monitor Server...")
    print("(MCP Server can be started separately)")
    print()
    
    try:
        start_webhook_server()
    except KeyboardInterrupt:
        print("\n👋 Shutting down servers...")
        sys.exit(0)

if __name__ == "__main__":
    main() 