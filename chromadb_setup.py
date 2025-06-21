#!/usr/bin/env python3
"""
ChromaDB Setup - Two Instances Configuration
This script sets up and manages two ChromaDB instances for different purposes.
"""

import chromadb
from chromadb.config import Settings
import os
import logging
from typing import Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaDBManager:
    """Manages two ChromaDB instances with different configurations"""
    
    def __init__(self):
        self.outlook_email_instance = None
        self.teams_chat_instance = None
        self.collections = {}
        
        # Create data directories
        self.outlook_email_dir = "./chromadb_data/outlook_email"
        self.teams_chat_dir = "./chromadb_data/teams_chat"
        
        os.makedirs(self.outlook_email_dir, exist_ok=True)
        os.makedirs(self.teams_chat_dir, exist_ok=True)
    
    def setup_outlook_email_instance(self, persist_directory: Optional[str] = None):
        """
        Setup Outlook Email Instance: For email storage and retrieval
        Configured for persistent storage with email-specific settings
        """
        try:
            settings = Settings(
                persist_directory=persist_directory or self.outlook_email_dir,
                anonymized_telemetry=False,  # Disable telemetry for privacy
                allow_reset=True,  # Allow database reset during development
            )
            
            self.outlook_email_instance = chromadb.PersistentClient(
                path=persist_directory or self.outlook_email_dir,
                settings=settings
            )
            
            # Create a collection for emails
            collection_name = "outlook_emails"
            try:
                self.collections["outlookEmail"] = self.outlook_email_instance.get_collection(collection_name)
                logger.info(f"Retrieved existing collection: {collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                self.collections["outlookEmail"] = self.outlook_email_instance.create_collection(
                    name=collection_name,
                    metadata={
                        "hnsw:space": "cosine",  # Use cosine similarity
                        "description": "Outlook email storage for email processing and retrieval"
                    }
                )
                logger.info(f"Created new collection: {collection_name}")
            
            logger.info("✅ ChromaDB Outlook Email Instance initialized successfully")
            return self.outlook_email_instance
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB Outlook Email Instance: {e}")
            raise
    
    def setup_teams_chat_instance(self, persist_directory: Optional[str] = None):
        """
        Setup Teams Chat Instance: For chat messages and conversations
        Configured for fast retrieval and chat data processing
        """
        try:
            settings = Settings(
                persist_directory=persist_directory or self.teams_chat_dir,
                anonymized_telemetry=False,
                allow_reset=True,
            )
            
            self.teams_chat_instance = chromadb.PersistentClient(
                path=persist_directory or self.teams_chat_dir,
                settings=settings
            )
            
            # Create a collection for chat messages
            collection_name = "teams_messages"
            try:
                self.collections["teamsChat"] = self.teams_chat_instance.get_collection(collection_name)
                logger.info(f"Retrieved existing collection: {collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                self.collections["teamsChat"] = self.teams_chat_instance.create_collection(
                    name=collection_name,
                    metadata={
                        "hnsw:space": "cosine",
                        "description": "Teams chat messages and conversations storage"
                    }
                )
                logger.info(f"Created new collection: {collection_name}")
            
            logger.info("✅ ChromaDB Teams Chat Instance initialized successfully")
            return self.teams_chat_instance
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB Teams Chat Instance: {e}")
            raise
    
    def initialize_both_instances(self):
        """Initialize both ChromaDB instances"""
        logger.info("🚀 Initializing ChromaDB instances...")
        
        outlook_email_instance = self.setup_outlook_email_instance()
        teams_chat_instance = self.setup_teams_chat_instance()
        
        logger.info("✅ Both ChromaDB instances initialized successfully!")
        return outlook_email_instance, teams_chat_instance
    
    def add_sample_data(self):
        """Add sample data to both instances for testing"""
        if not self.collections.get("outlookEmail") or not self.collections.get("teamsChat"):
            logger.error("Collections not initialized. Run initialize_both_instances() first.")
            return
        
        # Add sample data to Outlook Email instance
        outlook_emails = [
            "Subject: Meeting Tomorrow\nFrom: boss@company.com\nImportant meeting discussion about Q4 planning.",
            "Subject: Invoice Due\nFrom: billing@vendor.com\nYour monthly invoice is due for payment.",
            "Subject: Project Update\nFrom: team@company.com\nLatest updates on the AI development project."
        ]
        
        email_ids = [f"email_{i}" for i in range(len(outlook_emails))]
        
        self.collections["outlookEmail"].add(
            documents=outlook_emails,
            ids=email_ids,
            metadatas=[
                {"sender": "boss@company.com", "type": "meeting", "priority": "high"},
                {"sender": "billing@vendor.com", "type": "invoice", "priority": "urgent"},
                {"sender": "team@company.com", "type": "update", "priority": "medium"}
            ]
        )
        
        # Add sample data to Teams Chat instance
        teams_messages = [
            "Hey team, can we schedule a quick standup for tomorrow?",
            "The client presentation went really well! Great job everyone.",
            "I've uploaded the latest design mockups to the shared drive."
        ]
        
        chat_ids = [f"chat_{i}" for i in range(len(teams_messages))]
        
        self.collections["teamsChat"].add(
            documents=teams_messages,
            ids=chat_ids,
            metadatas=[
                {"user": "john_doe", "channel": "general", "timestamp": "2024-01-15T10:30:00Z"},
                {"user": "jane_smith", "channel": "project-alpha", "timestamp": "2024-01-15T14:20:00Z"},
                {"user": "mike_wilson", "channel": "design", "timestamp": "2024-01-15T16:45:00Z"}
            ]
        )
        
        logger.info("✅ Sample data added to both instances")
    
    def query_outlook_email(self, query_text: str, n_results: int = 3):
        """Query the Outlook Email instance"""
        if not self.collections.get("outlookEmail"):
            logger.error("Outlook Email collection not initialized")
            return None
        
        results = self.collections["outlookEmail"].query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results
    
    def query_teams_chat(self, query_text: str, n_results: int = 3):
        """Query the Teams Chat instance"""
        if not self.collections.get("teamsChat"):
            logger.error("Teams Chat collection not initialized")
            return None
        
        results = self.collections["teamsChat"].query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results
    
    def get_stats(self):
        """Get statistics for both instances"""
        stats = {}
        
        if self.collections.get("outlookEmail"):
            stats["outlookEmail"] = {
                "count": self.collections["outlookEmail"].count(),
                "name": self.collections["outlookEmail"].name
            }
        
        if self.collections.get("teamsChat"):
            stats["teamsChat"] = {
                "count": self.collections["teamsChat"].count(),
                "name": self.collections["teamsChat"].name
            }
        
        return stats
    
    def reset_instances(self):
        """Reset both instances (useful for development)"""
        try:
            if self.outlook_email_instance:
                self.outlook_email_instance.reset()
                logger.info("Outlook Email instance reset successfully")
            
            if self.teams_chat_instance:
                self.teams_chat_instance.reset() 
                logger.info("Teams Chat instance reset successfully")
            
            self.collections.clear()
            logger.info("✅ Both instances reset successfully")
            
        except Exception as e:
            logger.error(f"❌ Error resetting instances: {e}")


def main():
    """Main function to demonstrate ChromaDB setup"""
    print("🔧 Setting up ChromaDB instances...")
    
    # Initialize the manager
    manager = ChromaDBManager()
    
    try:
        # Initialize both instances
        outlook_email_instance, teams_chat_instance = manager.initialize_both_instances()
        
        # Add sample data
        print("\n📝 Adding sample data...")
        manager.add_sample_data()
        
        # Show statistics
        print("\n📊 Instance Statistics:")
        stats = manager.get_stats()
        for name, stat in stats.items():
            display_name = "Outlook Email" if name == "outlookEmail" else "Teams Chat"
            print(f"  {display_name}: {stat['count']} documents in '{stat['name']}'")
        
        # Demonstrate querying
        print("\n🔍 Query Examples:")
        
        # Query Outlook Email instance
        print("\n  Outlook Email Query:")
        email_results = manager.query_outlook_email("meeting")
        if email_results:
            for i, doc in enumerate(email_results['documents'][0]):
                print(f"    {i+1}. {doc[:80]}...")
        
        # Query Teams Chat instance  
        print("\n  Teams Chat Query:")
        chat_results = manager.query_teams_chat("presentation")
        if chat_results:
            for i, doc in enumerate(chat_results['documents'][0]):
                print(f"    {i+1}. {doc[:80]}...")
        
        print("\n✅ ChromaDB setup completed successfully!")
        print(f"💾 Data directories:")
        print(f"  Outlook Email: {manager.outlook_email_dir}")
        print(f"  Teams Chat: {manager.teams_chat_dir}")
        
        return manager
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        raise


if __name__ == "__main__":
    manager = main() 