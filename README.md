# InboxPilot
AI-Powered Email and Teams Message Automation System using Langflow

## Overview

InboxPilot is an intelligent automation system that monitors Microsoft Outlook emails and Teams messages, analyzes their content using AI, and automatically generates responses, creates tasks, schedules meetings, and performs other actions based on the content.

## Architecture

The system consists of three main components:

1. **Webhook Monitor** (`webhook_monitor/`) - FastAPI server that receives Microsoft Graph webhook notifications
2. **MCP Server** (`mcp_server/`) - Model Context Protocol server providing Microsoft Graph API tools
3. **Langflow Integration** - AI workflow engine for content analysis and action generation

## Features

- **Real-time Monitoring**: Receives instant notifications for new emails and Teams messages
- **AI Analysis**: Generates summaries, extracts action items, and analyzes sentiment
- **RAG Search**: Searches through previous messages using vector embeddings
- **Automated Actions**:
  - Send emails and Teams messages
  - Create Microsoft To Do tasks
  - Schedule Outlook calendar meetings
  - Search previous conversations
  - Generate intelligent responses

## Prerequisites

### Microsoft Azure Setup

1. **Register Azure AD Application**:
   - Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
   - Click "New registration"
   - Name: "InboxPilot"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Leave blank for now
   - Click "Register"

2. **Configure API Permissions**:
   - Go to "API permissions" → "Add a permission" → "Microsoft Graph" → "Application permissions"
   - Add these permissions:
     - `Mail.Read` - Read mail in all mailboxes
     - `Mail.Send` - Send mail as any user
     - `Mail.ReadWrite` - Read and write mail in all mailboxes
     - `Chat.Read.All` - Read all chat messages
     - `Chat.ReadWrite.All` - Read and write all chat messages
     - `Calendars.ReadWrite` - Read and write calendars in all mailboxes
     - `Tasks.ReadWrite` - Read and write tasks in all mailboxes
     - `User.Read.All` - Read all users' full profiles
   - Click "Grant admin consent"

3. **Create Client Secret**:
   - Go to "Certificates & secrets" → "New client secret"
   - Description: "InboxPilot Secret"
   - Expires: Choose appropriate duration
   - Copy the secret value (you won't see it again!)

4. **Note Required Values**:
   - Application (client) ID
   - Directory (tenant) ID
   - Client secret value

### Langflow Setup

1. **Install Langflow**:
   ```bash
   pip install langflow
   ```

2. **Start Langflow**:
   ```bash
   langflow run
   ```

3. **Create Webhook Flow**:
   - Open Langflow UI (usually http://localhost:7860)
   - Create a new flow with a Webhook Input component
   - Note the webhook URL for later configuration

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd InboxPilot
   ```

2. **Install MCP Server**:
   ```bash
   cd mcp_server
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Install Webhook Monitor dependencies**:
   ```bash
   cd ../webhook_monitor
   pip install fastapi uvicorn httpx cryptography
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```bash
   # Microsoft Graph API credentials
   MICROSOFT_TENANT_ID=your-tenant-id
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-client-secret

   # Webhook configuration
   WEBHOOK_BASE_URL=https://your-domain.com  # Your public webhook URL
   WEBHOOK_VALIDATION_TOKEN=your-validation-token
   LANGFLOW_WEBHOOK_URL=http://localhost:7860/api/v1/run/your-flow-id

   # Server configuration
   WEBHOOK_HOST=0.0.0.0
   WEBHOOK_PORT=8000
   ```

## Usage

### 1. Start the Webhook Monitor

```bash
cd webhook_monitor
python email_monitor.py
```

The webhook server will start on `http://localhost:8000`

### 2. Set up Webhook Subscriptions

Create subscriptions for users you want to monitor:

```bash
curl -X POST "http://localhost:8000/setup-subscriptions" \
  -H "Content-Type: application/json" \
  -d '["user1@yourdomain.com", "user2@yourdomain.com"]'
```

### 3. Use MCP Server with Langflow

The MCP server provides these tools for use in Langflow:

- `get_emails` - Retrieve emails from Outlook
- `send_email` - Send emails via Outlook
- `get_teams_messages` - Get Teams chat messages
- `send_teams_message` - Send Teams messages
- `search_emails` - Search through emails
- `create_todo_task` - Create Microsoft To Do tasks
- `schedule_meeting` - Schedule calendar meetings
- `get_user_chats` - List user's Teams chats

### 4. Example Langflow Workflows

We provide example workflows in the `langflow_examples/` directory:

**Complete InboxPilot Flow** (`complete_inboxpilot_flow.json`):
- **Dual Webhooks** - Separate inputs for emails and Teams messages
- **Dual Vector Stores** - Separate storage for emails and Teams
- **AI Analysis Pipeline** - Summarization, action extraction, and response generation
- **RAG + Web Search** - Context from previous messages and online sources
- **Conditional Routing** - Smart action routing based on content analysis
- **MCP Tool Integration** - Full Microsoft Graph API automation

**Advanced Email Flow** (`email_analysis_flow.json`):
- **Webhook Input** - Receives notifications from webhook monitor
- **Text Splitter** - Splits email/message content  
- **Vector Store** - Stores and searches message embeddings
- **LLM Model** - Analyzes content and generates responses

**To build the workflow:**

**Option 1: Import JSON (may need adjustments)**
1. Open Langflow UI (http://localhost:7860)
2. Try importing `complete_inboxpilot_flow.json`
3. Configure API keys and adjust components as needed

**Option 2: Build manually (recommended)**
1. Follow the step-by-step guide in `LANGFLOW_WORKFLOW_GUIDE.md`
2. Build the complete workflow component by component
3. This approach is more reliable and allows customization

**Required API Keys:**
- OpenAI API key (for LLMs and embeddings)
- Serper API key (for web search)
- Microsoft Graph credentials (configured in .env)

## API Endpoints

### Webhook Monitor Endpoints

- `POST /webhooks/email` - Receives email webhook notifications
- `POST /webhooks/teams` - Receives Teams webhook notifications
- `POST /setup-subscriptions` - Creates webhook subscriptions
- `GET /subscriptions` - Lists active subscriptions
- `DELETE /subscriptions/{id}` - Deletes a subscription
- `GET /health` - Health check

### MCP Server Tools

All tools require a `user_id` parameter (use "me" for current user):

```python
# Get recent emails
await call_tool("get_emails", {"user_id": "me", "top": 10})

# Send an email
await call_tool("send_email", {
    "user_id": "me",
    "to_recipients": ["recipient@example.com"],
    "subject": "AI Generated Response",
    "body": "This is an automated response."
})

# Create a task
await call_tool("create_todo_task", {
    "user_id": "me",
    "title": "Follow up on email",
    "description": "Respond to client inquiry",
    "due_date": "2024-01-15"
})
```

## Deployment

### Production Deployment

1. **Deploy webhook monitor** to a cloud platform (Azure, AWS, etc.)
2. **Configure public URL** for webhook notifications
3. **Set up SSL certificate** for HTTPS
4. **Configure environment variables** in production
5. **Set up monitoring and logging**

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r webhook_monitor/requirements.txt
RUN pip install -r mcp_server/requirements.txt

EXPOSE 8000

CMD ["python", "webhook_monitor/email_monitor.py"]
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify Azure AD app permissions are granted
   - Check client secret hasn't expired
   - Ensure tenant/client IDs are correct

2. **Webhook Validation Failures**:
   - Verify webhook URL is publicly accessible
   - Check validation token matches
   - Ensure HTTPS is used in production

3. **Subscription Errors**:
   - Check Microsoft Graph API limits
   - Verify webhook URL responds to validation requests
   - Ensure proper permissions for subscription resources

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check webhook subscription status:

```bash
curl http://localhost:8000/subscriptions
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review Microsoft Graph API documentation
- Open an issue on GitHub
