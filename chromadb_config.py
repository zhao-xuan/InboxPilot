"""
ChromaDB Configuration Settings
Centralized configuration for both ChromaDB instances
"""

import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ChromaDBInstanceConfig:
    """Configuration for a single ChromaDB instance"""
    name: str
    persist_directory: str
    port: int = None  # For server mode
    host: str = "localhost"
    collection_name: str = "default"
    embedding_function: str = "default"  # default, openai, sentence-transformers, etc.
    similarity_metric: str = "cosine"  # cosine, euclidean, ip
    description: str = ""
    settings: Dict[str, Any] = None

class ChromaDBConfig:
    """Main configuration class for ChromaDB setup"""
    
    def __init__(self, base_path: str = "./chromadb_data"):
        self.base_path = base_path
        self.instance_configs = self._get_default_configs()
        
    def _get_default_configs(self) -> Dict[str, ChromaDBInstanceConfig]:
        """Get default configurations for both instances"""
        return {
            "outlookEmail": ChromaDBInstanceConfig(
                name="outlookEmail",
                persist_directory=os.path.join(self.base_path, "outlook_email"),
                port=8001,  # For server mode
                collection_name="outlook_emails",
                embedding_function="default",
                similarity_metric="cosine",
                description="Outlook Email instance for email storage and retrieval",
                settings={
                    "anonymized_telemetry": False,
                    "allow_reset": True,
                    "hnsw_space": "cosine",
                    "hnsw_construction_ef": 200,
                    "hnsw_search_ef": 100,
                    "hnsw_M": 16
                }
            ),
            "teamsChat": ChromaDBInstanceConfig(
                name="teamsChat",
                persist_directory=os.path.join(self.base_path, "teams_chat"),
                port=8002,  # For server mode
                collection_name="teams_messages",
                embedding_function="default",
                similarity_metric="cosine",
                description="Teams Chat instance for chat messages and conversations",
                settings={
                    "anonymized_telemetry": False,
                    "allow_reset": True,
                    "hnsw_space": "cosine",
                    "hnsw_construction_ef": 150,  # Good performance for chat
                    "hnsw_search_ef": 75,         # Balanced search for chat
                    "hnsw_M": 12                  # Balanced memory usage for chat
                }
            )
        }
    
    def get_instance_config(self, instance_name: str) -> ChromaDBInstanceConfig:
        """Get configuration for a specific instance"""
        if instance_name not in self.instance_configs:
            raise ValueError(f"Instance '{instance_name}' not found. Available: {list(self.instance_configs.keys())}")
        return self.instance_configs[instance_name]
    
    def update_instance_config(self, instance_name: str, **kwargs):
        """Update configuration for a specific instance"""
        if instance_name not in self.instance_configs:
            raise ValueError(f"Instance '{instance_name}' not found")
        
        config = self.instance_configs[instance_name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                # Add to settings if not a direct attribute
                if config.settings is None:
                    config.settings = {}
                config.settings[key] = value
    
    def get_server_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get server configurations for running ChromaDB as separate servers"""
        server_configs = {}
        
        for name, config in self.instance_configs.items():
            server_configs[name] = {
                "host": config.host,
                "port": config.port,
                "persist_directory": config.persist_directory,
                "settings": config.settings or {}
            }
        
        return server_configs
    
    def create_directories(self):
        """Create all necessary directories"""
        for config in self.instance_configs.values():
            os.makedirs(config.persist_directory, exist_ok=True)
            print(f"✅ Created directory: {config.persist_directory}")

# Default configuration instance
DEFAULT_CONFIG = ChromaDBConfig()

# Environment-based configuration
class EnvironmentConfig:
    """Load configuration from environment variables"""
    
    @staticmethod
    def load_from_env() -> ChromaDBConfig:
        """Load configuration from environment variables"""
        config = ChromaDBConfig()
        
        # Outlook Email instance
        if os.getenv("CHROMADB_OUTLOOK_PORT"):
            config.update_instance_config("outlookEmail", port=int(os.getenv("CHROMADB_OUTLOOK_PORT")))
        
        if os.getenv("CHROMADB_OUTLOOK_PATH"):
            config.update_instance_config("outlookEmail", persist_directory=os.getenv("CHROMADB_OUTLOOK_PATH"))
        
        # Teams Chat instance
        if os.getenv("CHROMADB_TEAMS_PORT"):
            config.update_instance_config("teamsChat", port=int(os.getenv("CHROMADB_TEAMS_PORT")))
            
        if os.getenv("CHROMADB_TEAMS_PATH"):
            config.update_instance_config("teamsChat", persist_directory=os.getenv("CHROMADB_TEAMS_PATH"))
        
        # Global settings
        if os.getenv("CHROMADB_BASE_PATH"):
            config.base_path = os.getenv("CHROMADB_BASE_PATH")
        
        return config

if __name__ == "__main__":
    # Example usage and testing
    print("ChromaDB Configuration:")
    print("=" * 50)
    
    config = DEFAULT_CONFIG
    
    for name, instance_config in config.instance_configs.items():
        print(f"\n{name.upper()} Instance:")
        print(f"  Directory: {instance_config.persist_directory}")
        print(f"  Port: {instance_config.port}")
        print(f"  Collection: {instance_config.collection_name}")
        print(f"  Description: {instance_config.description}")
    
    print(f"\nServer configs:")
    server_configs = config.get_server_configs()
    for name, server_config in server_configs.items():
        print(f"  {name}: http://{server_config['host']}:{server_config['port']}")
    
    # Create directories
    print(f"\nCreating directories...")
    config.create_directories() 