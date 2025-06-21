#!/usr/bin/env python3
"""
ChromaDB Usage Examples
This file demonstrates how to use the two ChromaDB instances in your applications.
"""

from chromadb_setup import ChromaDBManager
import time

def example_outlook_email_storage():
    """Example: Using Outlook Email instance for email storage"""
    print("📧 Example 1: Outlook Email Storage")
    print("-" * 40)
    
    # Initialize manager
    manager = ChromaDBManager()
    manager.initialize_both_instances()
    
    # Add emails to Outlook Email instance
    emails = [
        "Subject: Q4 Planning Meeting\nFrom: ceo@company.com\nWe need to discuss our Q4 strategy and budget allocation.",
        "Subject: Security Alert\nFrom: security@company.com\nPlease update your password immediately for security compliance.",
        "Subject: New Project Kickoff\nFrom: pm@company.com\nExcited to announce the start of our new AI initiative project.",
        "Subject: Invoice Reminder\nFrom: accounts@vendor.com\nYour invoice #INV-2024-001 is due for payment."
    ]
    
    email_ids = [f"email_doc_{i}" for i in range(len(emails))]
    metadatas = [
        {"sender": "ceo@company.com", "type": "meeting", "priority": "high"},
        {"sender": "security@company.com", "type": "security", "priority": "urgent"},
        {"sender": "pm@company.com", "type": "project", "priority": "high"},
        {"sender": "accounts@vendor.com", "type": "invoice", "priority": "medium"}
    ]
    
    # Add to Outlook Email collection
    manager.collections["outlookEmail"].add(
        documents=emails,
        ids=email_ids,
        metadatas=metadatas
    )
    
    print(f"✅ Added {len(emails)} emails to Outlook Email instance")
    
    # Query the emails
    query_results = manager.query_outlook_email("project meeting", n_results=2)
    print(f"\n🔍 Query Results:")
    for i, doc in enumerate(query_results['documents'][0]):
        metadata = query_results['metadatas'][0][i]
        sender = metadata.get('sender', 'Unknown')
        email_type = metadata.get('type', 'Unknown')
        print(f"  {i+1}. {doc[:60]}... [From: {sender}, Type: {email_type}]")
    
    return manager

def example_teams_chat_system():
    """Example: Using Teams Chat instance for chat messages"""
    print("\n💬 Example 2: Teams Chat System")
    print("-" * 40)
    
    # Reuse manager from previous example or create new one
    manager = ChromaDBManager()
    manager.initialize_both_instances()
    
    # Simulate Teams chat messages
    chat_messages = [
        "Can everyone join the daily standup at 9 AM tomorrow? We need to discuss the sprint progress.",
        "Great work on the presentation! The client was really impressed with our approach.",
        "I've shared the updated design files in the Teams channel. Please review and provide feedback.",
        "Quick reminder: Code review session is scheduled for 3 PM today in Conference Room B."
    ]
    
    chat_ids = [f"teams_msg_{int(time.time())}_{i}" for i in range(len(chat_messages))]
    chat_metadata = [
        {"user": "alice_manager", "channel": "daily-standup", "timestamp": int(time.time())},
        {"user": "bob_sales", "channel": "client-feedback", "timestamp": int(time.time())},
        {"user": "carol_designer", "channel": "design-team", "timestamp": int(time.time())},
        {"user": "dave_tech", "channel": "code-review", "timestamp": int(time.time())}
    ]
    
    # Add to Teams Chat collection
    manager.collections["teamsChat"].add(
        documents=chat_messages,
        ids=chat_ids,
        metadatas=chat_metadata
    )
    
    print(f"✅ Added {len(chat_messages)} chat messages to Teams Chat")
    
    # Query chat messages
    chat_results = manager.query_teams_chat("meeting standup", n_results=1)
    if chat_results['documents'][0]:
        chat_message = chat_results['documents'][0][0]
        metadata = chat_results['metadatas'][0][0]
        print(f"\n💬 Found Chat Message: {chat_message}")
        print(f"   From: {metadata['user']} in #{metadata['channel']}")
    
    return manager

def example_hybrid_usage():
    """Example: Using both instances together"""
    print("\n🔄 Example 3: Hybrid Usage")
    print("-" * 40)
    
    manager = ChromaDBManager()
    manager.initialize_both_instances()
    
    # Scenario: Communication processing system
    # Outlook Email: Store important emails
    # Teams Chat: Store chat conversations
    
    # Important emails (Outlook storage)
    important_emails = [
        "Subject: Board Meeting Tomorrow - Please confirm your attendance for the quarterly board meeting.",
        "Subject: Invoice #12345 - Payment due for services rendered in January, please process immediately.",
        "Subject: Project Update - The new AI development project is 80% complete and on track for delivery."
    ]
    
    email_ids = [f"hybrid_email_{i}" for i in range(len(important_emails))]
    email_metadata = [
        {"sender": "board@company.com", "priority": "high", "type": "meeting"},
        {"sender": "billing@vendor.com", "priority": "urgent", "type": "invoice"},
        {"sender": "pm@company.com", "priority": "medium", "type": "update"}
    ]
    
    # Store in Outlook Email instance
    manager.collections["outlookEmail"].add(
        documents=important_emails,
        ids=email_ids,
        metadatas=email_metadata
    )
    
    # Related chat conversations (Teams storage)
    related_chats = [
        "Did everyone see the board meeting email? We should prepare our quarterly reports.",
        "The invoice processing is delayed. Can someone from finance help expedite this?",
        "Exciting news about the AI project! We're ahead of schedule and under budget."
    ]
    
    chat_ids = [f"hybrid_chat_{int(time.time())}_{i}" for i in range(len(related_chats))]
    chat_metadata = [
        {"user": "alice_manager", "channel": "management", "related_email": "hybrid_email_0"},
        {"user": "bob_finance", "channel": "finance", "related_email": "hybrid_email_1"},
        {"user": "carol_pm", "channel": "project-alpha", "related_email": "hybrid_email_2"}
    ]
    
    # Store in Teams Chat instance
    manager.collections["teamsChat"].add(
        documents=related_chats,
        ids=chat_ids,
        metadatas=chat_metadata
    )
    
    print("✅ Stored emails in Outlook Email instance")
    print("✅ Stored related chats in Teams Chat instance")
    
    # Query both instances
    print("\n📧 Finding urgent emails:")
    email_results = manager.query_outlook_email("invoice payment", n_results=1)
    if email_results['documents'][0]:
        urgent_email = email_results['documents'][0][0]
        print(f"   Found: {urgent_email[:50]}...")
    
    print("\n💬 Finding related chat discussions:")
    chat_results = manager.query_teams_chat("invoice processing", n_results=1)
    if chat_results['documents'][0]:
        related_chat = chat_results['documents'][0][0]
        metadata = chat_results['metadatas'][0][0]
        print(f"   Chat: {related_chat[:50]}...")
        print(f"   From: {metadata['user']} in #{metadata['channel']}")
    
    return manager

def show_instance_comparison():
    """Show the differences between the two instances"""
    print("\n⚖️  Instance Comparison")
    print("=" * 50)
    
    manager = ChromaDBManager()
    manager.initialize_both_instances()
    
    stats = manager.get_stats()
    
    print("OUTLOOK EMAIL Instance (Email storage):")
    print(f"  Purpose: Email storage and retrieval")
    print(f"  Documents: {stats.get('outlookEmail', {}).get('count', 0)}")
    print(f"  Collection: {stats.get('outlookEmail', {}).get('name', 'N/A')}")
    print(f"  Use cases: Important emails, email archives, email processing")
    
    print("\nTEAMS CHAT Instance (Chat storage):")
    print(f"  Purpose: Chat messages and conversations")
    print(f"  Documents: {stats.get('teamsChat', {}).get('count', 0)}")
    print(f"  Collection: {stats.get('teamsChat', {}).get('name', 'N/A')}")
    print(f"  Use cases: Team communications, chat history, conversation analysis")

def cleanup_example():
    """Example: Cleaning up data"""
    print("\n🧹 Example 4: Data Cleanup")
    print("-" * 40)
    
    manager = ChromaDBManager()
    manager.initialize_both_instances()
    
    print("Before cleanup:")
    stats = manager.get_stats()
    for name, stat in stats.items():
        print(f"  {name.capitalize()}: {stat['count']} documents")
    
    # Reset both instances (careful - this deletes all data!)
    print("\n⚠️  Resetting instances (deleting all data)...")
    manager.reset_instances()
    
    # Re-initialize after reset
    manager.initialize_both_instances()
    
    print("After cleanup:")
    stats = manager.get_stats()
    for name, stat in stats.items():
        print(f"  {name.capitalize()}: {stat['count']} documents")

def main():
    """Run all examples"""
    print("🚀 ChromaDB Usage Examples")
    print("=" * 50)
    
    try:
        # Run examples
        manager1 = example_document_storage()
        manager2 = example_caching_system()
        manager3 = example_hybrid_usage()
        
        # Show comparison
        show_instance_comparison()
        
        # Optional: Uncomment to test cleanup
        # cleanup_example()
        
        print("\n✅ All examples completed successfully!")
        print("\n📝 Next Steps:")
        print("  1. Integrate ChromaDBManager into your application")
        print("  2. Customize the collections and metadata for your use case")
        print("  3. Consider using the server setup for production environments")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        raise

if __name__ == "__main__":
    main() 