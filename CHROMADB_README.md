# ChromaDB Dual Instance Setup

This setup provides you with two ChromaDB instances configured for different purposes:

1. **Primary Instance**: For permanent document storage and retrieval
2. **Cache Instance**: For temporary data, API responses, and fast lookups

## 🚀 Quick Start

### 1. Install Dependencies

ChromaDB is already installed. If you need to reinstall:

```bash
pip3 install chromadb>=0.4.15
```

### 2. Run the Setup

```bash
# Test the embedded setup (recommended for development)
python3 chromadb_setup.py

# Or run the configuration test
python3 chromadb_config.py

# Try the usage examples
python3 chromadb_usage_example.py
```

## 📁 File Structure

```
InboxPilot/
├── chromadb_setup.py          # Main embedded setup (recommended)
├── chromadb_config.py         # Configuration management
├── chromadb_server_setup.py   # Server-based setup (advanced)
├── chromadb_usage_example.py  # Usage examples and demos
├── mcp_server/
│   └── requirements.txt       # Updated with ChromaDB dependency
└── chromadb_data/            # Data directories (auto-created)
    ├── instance_1/           # Primary instance data
    └── instance_2/           # Cache instance data
```

## 🔧 Configuration

### Default Configuration

- **Primary Instance**:
  - Directory: `./chromadb_data/instance_1`
  - Collection: `documents_primary`
  - Port: 8001 (for server mode)
  - Purpose: Long-term document storage

- **Cache Instance**:
  - Directory: `./chromadb_data/instance_2`
  - Collection: `cache_secondary`
  - Port: 8002 (for server mode)
  - Purpose: Temporary data and caching

### Environment Variables

You can customize the setup using environment variables:

```bash
export CHROMADB_PRIMARY_PORT=8001
export CHROMADB_CACHE_PORT=8002
export CHROMADB_PRIMARY_PATH="./data/primary"
export CHROMADB_CACHE_PATH="./data/cache"
export CHROMADB_BASE_PATH="./custom_chromadb"
```

## 💻 Usage Examples

### Basic Usage (Embedded Mode)

```python
from chromadb_setup import ChromaDBManager

# Initialize both instances
manager = ChromaDBManager()
manager.initialize_both_instances()

# Add documents to primary instance
documents = ["Document 1 content", "Document 2 content"]
ids = ["doc1", "doc2"]
metadatas = [{"type": "article"}, {"type": "report"}]

manager.collections["primary"].add(
    documents=documents,
    ids=ids,
    metadatas=metadatas
)

# Query documents
results = manager.query_primary("search query", n_results=3)
print(results['documents'][0])  # Retrieved documents

# Use cache for temporary data
cache_data = ["Temporary result 1", "API response cache"]
cache_ids = ["temp1", "api_cache1"]

manager.collections["cache"].add(
    documents=cache_data,
    ids=cache_ids,
    metadatas=[{"ttl": 3600}, {"ttl": 1800}]
)

# Query cache
cache_results = manager.query_cache("API response", n_results=1)
```

### Advanced Usage

```python
# Get statistics
stats = manager.get_stats()
print(f"Primary: {stats['primary']['count']} documents")
print(f"Cache: {stats['cache']['count']} documents")

# Reset instances (development only)
manager.reset_instances()
```

## 🖥️ Server Mode (Advanced)

For production environments, you can run ChromaDB as separate server instances:

```bash
# Start both server instances
python3 chromadb_server_setup.py
```

This will start:
- Primary server: `http://localhost:8001`
- Cache server: `http://localhost:8002`

### Client Connection (Server Mode)

```python
import chromadb

# Connect to primary server
primary_client = chromadb.HttpClient(host="localhost", port=8001)
primary_collection = primary_client.get_or_create_collection("documents_primary")

# Connect to cache server
cache_client = chromadb.HttpClient(host="localhost", port=8002)
cache_collection = cache_client.get_or_create_collection("cache_secondary")
```

## 🎯 Use Cases

### Primary Instance (Long-term Storage)
- Important documents and articles
- Knowledge base content
- Email archives
- Research papers
- User-generated content

### Cache Instance (Temporary Storage)
- API response caching
- Session data
- Temporary processing results
- Search result caching
- User interaction data

## 🔍 API Endpoints (Server Mode)

When running in server mode, you can access the REST APIs:

- **Primary Server API**: `http://localhost:8001/docs`
- **Cache Server API**: `http://localhost:8002/docs`

## 🛠️ Customization

### Adding Custom Embedding Functions

```python
# Example with different embedding functions
from chromadb.utils import embedding_functions

# OpenAI embeddings (requires API key)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-api-key",
    model_name="text-embedding-ada-002"
)

# Create collection with custom embedding
collection = client.create_collection(
    name="custom_collection",
    embedding_function=openai_ef
)
```

### Configuring HNSW Parameters

```python
# High performance setup (more memory, faster search)
collection = client.create_collection(
    name="high_perf_collection",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:M": 32,                    # More connections
        "hnsw:construction_ef": 400,     # Better indexing
        "hnsw:search_ef": 200            # Better search quality
    }
)

# Memory efficient setup (less memory, slightly slower)
collection = client.create_collection(
    name="memory_efficient_collection",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:M": 8,                     # Fewer connections
        "hnsw:construction_ef": 100,     # Faster indexing
        "hnsw:search_ef": 50             # Faster search
    }
)
```

## 📊 Monitoring and Maintenance

### Health Checks

```python
# Check instance health
stats = manager.get_stats()
for name, stat in stats.items():
    print(f"{name}: {stat['count']} documents in '{stat['name']}'")

# Server mode health check
import requests
response = requests.get("http://localhost:8001/api/v1/heartbeat")
print(f"Primary server status: {response.status_code}")
```

### Data Cleanup

```python
# Reset all data (development only)
manager.reset_instances()

# Delete specific documents
collection.delete(ids=["doc1", "doc2"])

# Clear entire collection
collection.delete()  # Deletes all documents
```

## 🔒 Security Considerations

1. **Network Security**: In production, bind servers to specific interfaces
2. **Authentication**: ChromaDB supports token-based authentication
3. **Data Encryption**: Consider encrypting data at rest
4. **Access Control**: Implement proper access controls for your use case

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Check what's using the port
   lsof -i :8001
   # Kill the process or change the port in configuration
   ```

2. **Permission Errors**:
   ```bash
   # Ensure proper permissions for data directories
   chmod -R 755 ./chromadb_data/
   ```

3. **Memory Issues**:
   - Reduce HNSW parameters for lower memory usage
   - Use the cache instance for temporary data only
   - Implement data rotation policies

### Logs and Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed ChromaDB operations
```

## 📝 Integration Examples

### Email Processing System

```python
# Store important emails in primary
manager.collections["primary"].add(
    documents=["Important email content..."],
    ids=["email_123"],
    metadatas=[{"sender": "boss@company.com", "priority": "high"}]
)

# Cache processing results
manager.collections["cache"].add(
    documents=["Sentiment: Positive, Urgency: High"],
    ids=["analysis_123"],
    metadatas=[{"type": "sentiment", "email_id": "email_123"}]
)
```

### Document Search System

```python
# Index documents
documents = load_documents()  # Your document loading function
manager.collections["primary"].add(
    documents=[doc.content for doc in documents],
    ids=[doc.id for doc in documents],
    metadatas=[doc.metadata for doc in documents]
)

# Search with filtering
results = manager.collections["primary"].query(
    query_texts=["user search query"],
    n_results=10,
    where={"category": "research"}  # Filter by metadata
)
```

## 🚀 Next Steps

1. **Integrate into Your Application**: Use the `ChromaDBManager` class in your main application
2. **Customize Collections**: Modify collection names and metadata schemas for your use case
3. **Scale Up**: Consider server mode for production deployments
4. **Monitor Performance**: Implement logging and monitoring for your specific needs
5. **Backup Strategy**: Plan for data backup and recovery procedures

## 📞 Support

For ChromaDB-specific issues, check the [official documentation](https://docs.trychroma.com/).

For issues with this setup, review the example files and ensure all dependencies are properly installed. 