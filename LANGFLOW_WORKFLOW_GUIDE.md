# Complete InboxPilot Langflow Workflow Guide

This guide explains how to build the complete InboxPilot workflow in Langflow that monitors MS Outlook and Teams, analyzes content, and takes automated actions.

## 🏗️ Workflow Architecture

The workflow consists of these main stages:

1. **Input Stage**: Webhook receivers for emails and Teams messages
2. **Storage Stage**: Text splitting and vector storage (separate stores for emails/Teams)
3. **Analysis Stage**: AI-powered summarization and action item extraction
4. **Context Stage**: RAG retrieval and web search for additional context
5. **Action Stage**: AI-generated actions routed to appropriate Microsoft Graph APIs

## 📋 Required Components

### Input Components
- **2x Webhook Components**: Separate webhooks for email and Teams notifications
- **2x Text Splitters**: Process email and Teams content separately

### Storage Components  
- **1x OpenAI Embeddings**: Generate embeddings for vector storage
- **2x Chroma Vector Stores**: Separate storage for emails and Teams messages

### Analysis Components
- **3x OpenAI LLM Models**: 
  - Content Summarizer
  - Action Item Extractor  
  - Action Generator
- **1x Vector Store Retriever**: RAG search through previous messages
- **1x Web Search**: Online search for additional context

### Action Components
- **1x Conditional Router**: Route actions based on content analysis
- **4x MCP Tools**: Microsoft Graph API integrations
  - Send Email
  - Send Teams Message
  - Create Todo Task
  - Schedule Meeting

## 🔧 Step-by-Step Build Instructions

### Step 1: Create Input Webhooks

1. **Add Webhook Component** (Email Input)
   - Drag "Webhook" component to canvas
   - Position: (100, 100)
   - Rename to "Email Webhook"
   - Configure data field to receive email notifications

2. **Add Webhook Component** (Teams Input)
   - Drag another "Webhook" component to canvas
   - Position: (100, 300)
   - Rename to "Teams Webhook"
   - Configure data field to receive Teams notifications

### Step 2: Set Up Text Processing

3. **Add Text Splitter** (Email)
   - Drag "RecursiveCharacterTextSplitter" component
   - Position: (500, 100)
   - Configure:
     - Chunk Size: 1000
     - Chunk Overlap: 200
   - Connect from Email Webhook

4. **Add Text Splitter** (Teams)
   - Drag another "RecursiveCharacterTextSplitter" component
   - Position: (500, 300)
   - Configure:
     - Chunk Size: 500
     - Chunk Overlap: 100
   - Connect from Teams Webhook

### Step 3: Configure Embeddings and Vector Storage

5. **Add OpenAI Embeddings**
   - Drag "OpenAIEmbeddings" component
   - Position: (900, 200)
   - Configure:
     - Model: text-embedding-ada-002
     - Add your OpenAI API key

6. **Add Email Vector Store**
   - Drag "Chroma" component
   - Position: (1300, 100)
   - Configure:
     - Collection Name: "email_messages"
     - Persist Directory: "./chroma_db_emails"
   - Connect embeddings and email text splitter

7. **Add Teams Vector Store**
   - Drag another "Chroma" component
   - Position: (1300, 300)
   - Configure:
     - Collection Name: "teams_messages"
     - Persist Directory: "./chroma_db_teams"
   - Connect embeddings and Teams text splitter

### Step 4: Build Analysis Pipeline

8. **Add Content Summarizer**
   - Drag "OpenAI" component
   - Position: (500, 600)
   - Configure:
     - Model: gpt-4
     - Temperature: 0.1
     - System Message: "You are an AI assistant that summarizes emails and messages. Provide a concise summary highlighting the main points, sender, and purpose of the message."
   - Connect from Email Webhook

9. **Add Action Item Extractor**
   - Drag another "OpenAI" component
   - Position: (900, 600)
   - Configure:
     - Model: gpt-4
     - Temperature: 0.2
     - System Message: "You are an AI assistant that extracts action items from emails and messages. Identify specific tasks, deadlines, requests, and follow-up actions. Format as a numbered list."
   - Connect from Content Summarizer

### Step 5: Add Context Retrieval

10. **Add RAG Retriever**
    - Drag "VectorStoreRetriever" component
    - Position: (1300, 600)
    - Configure:
      - Search Type: similarity
      - Search Parameters: {"k": 5}
    - Connect from Email Vector Store and Action Extractor

11. **Add Web Search**
    - Drag "SerperSearchRun" component (or similar web search)
    - Position: (1700, 600)
    - Configure:
      - Add Serper API key
      - Number of Results: 3
    - Connect from Action Extractor

### Step 6: Create Action Generator

12. **Add Action Generator**
    - Drag "OpenAI" component
    - Position: (2100, 400)
    - Configure:
      - Model: gpt-4
      - Temperature: 0.3
      - System Message: "You are an AI assistant that generates specific actions based on email/message analysis, previous context, and web search results. Suggest concrete actions using Microsoft Graph APIs for Teams, Outlook, and Todo. Format as JSON with action type, parameters, and reasoning."
    - Connect from RAG Retriever and Web Search

### Step 7: Add Conditional Routing

13. **Add Conditional Router**
    - Drag "ConditionalRouter" component
    - Position: (2100, 800)
    - Configure routing conditions:
      - contains('email') → Send Email
      - contains('meeting') → Schedule Meeting
      - contains('task') → Create Task
      - contains('urgent') → Send Teams Message
    - Connect from Action Generator

### Step 8: Configure MCP Tools

14. **Add Send Email Tool**
    - Drag "MCPTool" component
    - Position: (2500, 200)
    - Configure:
      - Server Name: "microsoft-graph"
      - Tool Name: "send_email"
    - Connect from Conditional Router

15. **Add Send Teams Message Tool**
    - Drag "MCPTool" component
    - Position: (2500, 400)
    - Configure:
      - Server Name: "microsoft-graph"
      - Tool Name: "send_teams_message"
    - Connect from Conditional Router

16. **Add Create Task Tool**
    - Drag "MCPTool" component
    - Position: (2500, 600)
    - Configure:
      - Server Name: "microsoft-graph"
      - Tool Name: "create_todo_task"
    - Connect from Conditional Router

17. **Add Schedule Meeting Tool**
    - Drag "MCPTool" component
    - Position: (2500, 800)
    - Configure:
      - Server Name: "microsoft-graph"
      - Tool Name: "schedule_meeting"
    - Connect from Conditional Router

## 🔑 Required API Keys

Before running the workflow, ensure you have:

1. **OpenAI API Key** - For LLM models and embeddings
2. **Serper API Key** - For web search (or alternative search provider)
3. **Microsoft Graph Credentials** - For MCP server (configured in your .env file)

## 🔗 Webhook Configuration

Connect your webhook URLs to the InboxPilot webhook monitor:

1. **Email Webhook URL**: Use in `LANGFLOW_WEBHOOK_URL` for email notifications
2. **Teams Webhook URL**: Configure separate endpoint for Teams notifications

## 🚀 Testing the Workflow

1. **Start all services**:
   ```bash
   # Terminal 1: Webhook Monitor
   cd webhook_monitor && python email_monitor.py
   
   # Terminal 2: MCP Server
   cd mcp_server && python microsoft_graph_server.py
   
   # Terminal 3: Langflow
   langflow run
   ```

2. **Send test email** to trigger the workflow

3. **Monitor the flow** in Langflow UI to see:
   - Email processing and storage
   - AI analysis and action extraction
   - RAG retrieval and web search
   - Action generation and execution

## 🎯 Expected Workflow Behavior

When a new email arrives:

1. **Webhook receives** email notification
2. **Text splitter** chunks the email content
3. **Vector store** saves email embeddings
4. **Summarizer** creates email summary
5. **Action extractor** identifies action items
6. **RAG retriever** finds relevant previous emails
7. **Web search** gathers additional context
8. **Action generator** creates specific actions
9. **Router** determines appropriate action type
10. **MCP tools** execute Microsoft Graph API calls

## 🔧 Customization Options

- **Adjust chunk sizes** for different content types
- **Modify system prompts** for different analysis styles
- **Add more conditions** to the router for complex routing
- **Include additional MCP tools** for more Microsoft Graph operations
- **Add email/Teams filters** for specific senders or keywords

## 🐛 Troubleshooting

- **Webhook not triggering**: Check webhook URL configuration
- **Vector store errors**: Ensure Chroma dependencies are installed
- **MCP tool failures**: Verify Microsoft Graph credentials
- **LLM errors**: Check OpenAI API key and rate limits
- **Search failures**: Verify Serper API key

This complete workflow provides a production-ready foundation for intelligent email and Teams automation with AI analysis and automated responses. 