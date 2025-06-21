#!/usr/bin/env python3
"""
Test script to demonstrate local ChromaDB instances
This script shows how to connect to and query the outlookEmail and teamsChat instances
"""

from chromadb_setup import ChromaDBManager
import json

def test_local_chromadb():
    """Test the local ChromaDB instances"""
    print("🔍 Testing Local ChromaDB Instances")
    print("=" * 50)
    
    # Initialize manager and connect to existing instances
    manager = ChromaDBManager()
    manager.initialize_both_instances()
    
    # Show current statistics
    print("\n📊 Current Statistics:")
    stats = manager.get_stats()
    for name, stat in stats.items():
        display_name = "Outlook Email" if name == "outlookEmail" else "Teams Chat"
        print(f"  {display_name}: {stat['count']} documents in '{stat['name']}'")
    
    # Test Outlook Email queries
    print("\n📧 Testing Outlook Email Queries:")
    test_queries = ["meeting", "invoice", "project"]
    
    for query in test_queries:
        results = manager.query_outlook_email(query, n_results=1)
        if results and results['documents'][0]:
            doc = results['documents'][0][0]
            metadata = results['metadatas'][0][0]
            print(f"  Query '{query}': {doc[:50]}... [From: {metadata.get('sender', 'Unknown')}]")
    
    # Test Teams Chat queries  
    print("\n💬 Testing Teams Chat Queries:")
    chat_queries = ["standup", "presentation", "design"]
    
    for query in chat_queries:
        results = manager.query_teams_chat(query, n_results=1)
        if results and results['documents'][0]:
            doc = results['documents'][0][0]
            metadata = results['metadatas'][0][0]
            print(f"  Query '{query}': {doc[:50]}... [User: {metadata.get('user', 'Unknown')}]")
    
    # Test adding new data
    print("\n➕ Adding New Test Data:")
    
    # Add a new email
    new_email = "Subject: Urgent Security Update\nFrom: security@company.com\nPlease update your system immediately."
    manager.collections["outlookEmail"].add(
        documents=[new_email],
        ids=["test_email_new"],
        metadatas=[{"sender": "security@company.com", "type": "security", "priority": "urgent"}]
    )
    print("  ✅ Added new email to Outlook Email instance")
    
    # Add a new chat message
    new_chat = "Thanks everyone for the great work this week! Looking forward to next sprint."
    manager.collections["teamsChat"].add(
        documents=[new_chat],
        ids=["test_chat_new"],
        metadatas=[{"user": "manager_jane", "channel": "general", "timestamp": "2024-01-16T17:00:00Z"}]
    )
    print("  ✅ Added new chat message to Teams Chat instance")
    
    # Show updated statistics
    print("\n📊 Updated Statistics:")
    stats = manager.get_stats()
    for name, stat in stats.items():
        display_name = "Outlook Email" if name == "outlookEmail" else "Teams Chat"
        print(f"  {display_name}: {stat['count']} documents in '{stat['name']}'")
    
    # Test the new data
    print("\n🔍 Testing New Data:")
    security_results = manager.query_outlook_email("security update", n_results=1)
    if security_results and security_results['documents'][0]:
        print(f"  Security email found: {security_results['documents'][0][0][:50]}...")
    
    sprint_results = manager.query_teams_chat("sprint work", n_results=1)
    if sprint_results and sprint_results['documents'][0]:
        print(f"  Sprint chat found: {sprint_results['documents'][0][0][:50]}...")
    
    print("\n✅ Local ChromaDB test completed successfully!")
    return manager

if __name__ == "__main__":
    test_local_chromadb() 