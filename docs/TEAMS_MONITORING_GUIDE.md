# Teams Monitoring with Microsoft Graph API

This guide explains how to set up and use Teams message monitoring in InboxPilot using Microsoft Graph API webhooks.

## Overview

The Teams monitoring system provides real-time notifications for:
- **Teams Chat Messages** - Direct messages and group chats
- **Teams Channel Messages** - Messages posted in team channels
- **Email Messages** - Outlook emails (existing functionality)

## Architecture

```
Microsoft Teams/Outlook
         ↓ (Webhook notifications)
    Webhook Monitor Server
         ↓ (Processed data)
      Langflow Workflow
         ↓ (AI analysis)
    MCP Server Actions
```

## Setup Requirements

### 1. Microsoft Graph App Registration

Your Azure AD application needs these **API permissions**:

#### Application Permissions (for service-to-service)
```
Mail.Read                    - Read emails
Mail.ReadWrite              - Read and send emails
Chat.Read.All               - Read all chat messages
Chat.ReadWrite.All          - Read and write chat messages
ChannelMessage.Read.All     - Read channel messages
Team.ReadBasic.All          - Read basic team info
User.Read.All               - Read user profiles
```

#### Delegated Permissions (if using user context)
```
Mail.Read                   - Read user's emails
Chat.Read                   - Read user's chats
ChannelMessage.Read.All     - Read channel messages
Team.ReadBasic.All          - Read teams user belongs to
```

### 2. Admin Consent

**CRITICAL**: All permissions must have **admin consent** granted in the Azure portal.

### 3. Environment Configuration

Update your `.env` file with the Teams monitoring settings:

```bash
# Microsoft Graph Configuration
MICROSOFT_TENANT_ID=your_tenant_id
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret

# Webhook Configuration
WEBHOOK_BASE_URL=https://your-domain.com
WEBHOOK_VALIDATION_TOKEN=your_validation_token

# Teams Monitoring
TEAMS_MONITORING_ENABLED=true
TEAMS_CHAT_MONITORING=true
TEAMS_CHANNEL_MONITORING=true
```

## Webhook Endpoints

The enhanced webhook server provides these endpoints:

### Notification Endpoints
- `POST /webhooks/email` - Email notifications
- `POST /webhooks/teams/chat` - Teams chat notifications  
- `POST /webhooks/teams/channel` - Teams channel notifications

### Management Endpoints
- `POST /setup-subscriptions` - Create webhook subscriptions
- `GET /subscriptions` - List active subscriptions
- `DELETE /subscriptions/{id}` - Delete subscription
- `GET /users/{user_id}/teams` - Get user's teams
- `GET /teams/{team_id}/channels` - Get team channels
- `GET /health` - Health check

## Setting Up Teams Monitoring

### Method 1: Using the Setup Script

```bash
# 1. Start the webhook server
cd webhook_monitor
python email_monitor.py

# 2. Run the setup script
cd ../scripts
python setup_teams_monitoring.py
```

The script will:
1. Check webhook server health
2. Set up email and Teams chat subscriptions for users
3. Discover user teams
4. Optionally set up channel subscriptions
5. Display all active subscriptions

### Method 2: Manual API Calls

#### Setup User Subscriptions
```bash
curl -X POST http://localhost:8000/setup-subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["user1@company.com", "user2@company.com"],
    "team_ids": [],
    "include_channels": false
  }'
```

#### Setup Team Channel Subscriptions
```bash
curl -X POST http://localhost:8000/setup-subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [],
    "team_ids": ["team-id-1", "team-id-2"],
    "include_channels": true
  }'
```

## Webhook Data Format

### Teams Chat Message
```json
{
  "type": "teams_chat",
  "change_type": "created",
  "chat_id": "19:chat-id",
  "message_id": "message-id",
  "timestamp": "2024-01-15T10:30:00Z",
  "message_details": {
    "id": "message-id",
    "messageType": "message",
    "from": {
      "user": {
        "id": "user-id",
        "displayName": "John Doe",
        "userIdentityType": "aadUser"
      }
    },
    "body": {
      "content": "Hello team!",
      "contentType": "text"
    },
    "createdDateTime": "2024-01-15T10:30:00Z",
    "mentions": [],
    "attachments": []
  }
}
```

### Teams Channel Message
```json
{
  "type": "teams_channel",
  "change_type": "created",
  "team_id": "team-id",
  "channel_id": "channel-id",
  "message_id": "message-id",
  "timestamp": "2024-01-15T10:30:00Z",
  "message_details": {
    "id": "message-id",
    "messageType": "message",
    "from": {
      "user": {
        "id": "user-id",
        "displayName": "Jane Smith"
      }
    },
    "body": {
      "content": "Project update: We're on track!",
      "contentType": "html"
    },
    "createdDateTime": "2024-01-15T10:30:00Z",
    "mentions": [
      {
        "id": 0,
        "mentionText": "John Doe",
        "mentioned": {
          "user": {
            "id": "mentioned-user-id",
            "displayName": "John Doe"
          }
        }
      }
    ]
  }
}
```

## Langflow Integration

### Webhook Input Configuration

In your Langflow workflow, configure the webhook inputs to handle different message types:

#### Email Webhook Input
- **Display Name**: "Email Webhook"
- **Input Field**: "Email Data"
- **Info**: "Email webhook data from Microsoft Graph"

#### Teams Chat Webhook Input  
- **Display Name**: "Teams Chat Webhook"
- **Input Field**: "Teams Chat Data"
- **Info**: "Teams chat webhook data from Microsoft Graph"

#### Teams Channel Webhook Input
- **Display Name**: "Teams Channel Webhook"  
- **Input Field**: "Teams Channel Data"
- **Info**: "Teams channel webhook data from Microsoft Graph"

### Processing Different Message Types

Use conditional logic in Langflow to handle different message types:

```python
# In a Python component
def process_message(data):
    message_type = data.get("type")
    
    if message_type == "email":
        return process_email(data)
    elif message_type == "teams_chat":
        return process_teams_chat(data)
    elif message_type == "teams_channel":
        return process_teams_channel(data)
    else:
        return "Unknown message type"

def process_teams_chat(data):
    details = data.get("message_details", {})
    content = details.get("body", {}).get("content", "")
    sender = details.get("from", {}).get("user", {}).get("displayName", "Unknown")
    
    return f"Teams Chat from {sender}: {content}"
```

## Monitoring and Troubleshooting

### Check Subscription Status
```bash
curl http://localhost:8000/subscriptions
```

### View Server Logs
```bash
# Check webhook server logs
tail -f webhook_monitor/logs/webhook.log

# Check for specific errors
grep "ERROR" webhook_monitor/logs/webhook.log
```

### Common Issues

#### 1. Permission Errors
```
Error: Insufficient privileges to complete the operation
```
**Solution**: Ensure admin consent is granted for all required permissions.

#### 2. Webhook Validation Failures
```
Error: Webhook validation failed
```
**Solution**: Check that `WEBHOOK_BASE_URL` is publicly accessible and uses HTTPS.

#### 3. Subscription Expiration
Subscriptions expire after 24 hours and need renewal.
**Solution**: Implement automatic renewal or manually renew:
```bash
curl -X PATCH http://localhost:8000/subscriptions/{subscription_id}
```

### Testing Webhooks Locally

For local development, use a tool like ngrok to expose your webhook server:

```bash
# Install ngrok
npm install -g ngrok

# Expose local webhook server
ngrok http 8000

# Update WEBHOOK_BASE_URL in .env
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io
```

## Security Considerations

1. **HTTPS Required**: Microsoft Graph requires HTTPS for webhook endpoints in production
2. **Validation Token**: Use a secure, random validation token
3. **Request Validation**: Implement proper request signature validation
4. **Rate Limiting**: Monitor and implement rate limiting for webhook endpoints
5. **Access Control**: Restrict access to webhook management endpoints

## Performance Optimization

1. **Batch Processing**: Process multiple notifications in batches
2. **Async Processing**: Use async/await for all Graph API calls
3. **Caching**: Cache access tokens and team/channel information
4. **Error Handling**: Implement retry logic with exponential backoff

## Next Steps

1. **Start the webhook server**: `cd webhook_monitor && python email_monitor.py`
2. **Run the setup script**: `cd scripts && python setup_teams_monitoring.py`
3. **Configure Langflow**: Import the workflow JSON and configure webhooks
4. **Test the integration**: Send test messages in Teams and verify processing
5. **Monitor and tune**: Adjust processing logic based on your needs

The Teams monitoring system is now ready to capture and process Teams messages alongside your existing email monitoring! 