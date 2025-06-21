# Microsoft Graph Subscription Setup Guide

## 🎯 **Overview**

This guide walks you through creating Microsoft Graph subscriptions to monitor:
- **Email**: New messages in Outlook inbox
- **Teams Chat**: Direct messages and group chats  
- **Teams Channels**: Channel messages across teams

## 📋 **Prerequisites**

### 1. Azure AD App Registration
Your Azure AD app needs these **Application Permissions** (requires admin consent):

**For Email:**
- `Mail.Read` or `Mail.ReadWrite`

**For Teams:**
- `Chat.Read.All` (for chat messages)
- `ChannelMessage.Read.All` (for channel messages)
- `Team.ReadBasic.All` (for team information)
- `User.Read.All` (for user information)

### 2. Environment Configuration
Update your `.env` file with:
```bash
# Your Azure AD app credentials
MICROSOFT_TENANT_ID=your_tenant_id
MICROSOFT_CLIENT_ID=your_client_id  
MICROSOFT_CLIENT_SECRET=your_client_secret

# Your publicly accessible webhook URL
WEBHOOK_BASE_URL=https://your-ngrok-subdomain.ngrok.io

# Subscription settings
SUBSCRIPTION_CLIENT_STATE=your-secret-client-state-value
SUBSCRIPTION_EXPIRATION_HOURS=24
```

### 3. Public Webhook Endpoint
Your webhook server must be publicly accessible via HTTPS:

**For Local Development:**
```bash
# Install ngrok
npm install -g ngrok
# or download from https://ngrok.com/

# Expose your local server (port 8000)
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update WEBHOOK_BASE_URL in .env
```

**For Production:**
Use your actual domain with HTTPS certificate.

## 🚀 **Setup Steps**

### Step 1: Start the Webhook Server
```bash
# Navigate to your project directory
cd /Users/tomzhao/Desktop/InboxPilot

# Start the webhook monitor
python -m uvicorn webhook_monitor.email_monitor:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Use the Subscription Setup Script
```bash
# Run the interactive setup script
python scripts/setup_subscriptions.py
```

The script will guide you through:
1. Testing your webhook endpoints
2. Creating subscriptions for email and Teams
3. Managing existing subscriptions

### Step 3: Alternative - Manual API Calls

**Create Email Subscription:**
```bash
curl -X POST "http://localhost:8000/subscriptions/setup-email" \
  -H "Content-Type: application/json"
```

**Create Teams Subscriptions:**
```bash
curl -X POST "http://localhost:8000/subscriptions/setup-teams" \
  -H "Content-Type: application/json"
```

**List Active Subscriptions:**
```bash
curl -X GET "http://localhost:8000/subscriptions/list"
```

## 🔧 **Webhook Endpoints**

Microsoft Graph will send notifications to these endpoints:

| Resource Type | Endpoint | Purpose |
|---------------|----------|---------|
| Email | `/webhooks/email` | Outlook inbox messages |
| Teams Chat | `/webhooks/teams/chat` | Direct & group chat messages |
| Teams Channel | `/webhooks/teams/channel` | Channel messages |

## 📊 **Subscription Resources**

### Email Subscription
```json
{
  "resource": "me/mailFolders('Inbox')/messages",
  "changeType": "created",
  "notificationUrl": "https://your-domain.com/webhooks/email"
}
```

### Teams Chat Subscription  
```json
{
  "resource": "chats/getAllMessages",
  "changeType": "created", 
  "notificationUrl": "https://your-domain.com/webhooks/teams/chat"
}
```

### Teams Channel Subscription
```json
{
  "resource": "teams/getAllMessages",
  "changeType": "created",
  "notificationUrl": "https://your-domain.com/webhooks/teams/channel"
}
```

## 🔄 **Subscription Lifecycle**

### Validation Process
1. Microsoft Graph sends validation token to your webhook URL
2. Your endpoint must return the token in plain text within 10 seconds
3. Subscription is created if validation succeeds

### Expiration & Renewal
- Subscriptions expire after 24 hours (configurable)
- Renew before expiration to continue receiving notifications
- Use the renewal endpoint: `POST /subscriptions/{id}/renew`

### Monitoring
- Check subscription status: `GET /subscriptions/list`
- View webhook server logs for debugging
- Monitor Microsoft Graph service health

## 🛠️ **Troubleshooting**

### Common Issues

**"Webhook endpoint not accessible"**
- Ensure your server is running on the correct port
- Check that ngrok is forwarding to the right port
- Verify WEBHOOK_BASE_URL in .env matches ngrok URL

**"Failed to get access token"**
- Verify Azure AD app credentials in .env
- Check that app has required permissions
- Ensure admin consent has been granted

**"Subscription creation failed"**
- Confirm webhook endpoint responds to validation
- Check that resource path is correct
- Verify app permissions match subscription requirements

**"No notifications received"**
- Check subscription expiration date
- Verify webhook endpoint is still accessible
- Monitor webhook server logs for incoming requests

### Debug Commands

**Test webhook accessibility:**
```bash
curl -X GET "https://your-ngrok-subdomain.ngrok.io/webhooks/email"
```

**Check subscription status:**
```bash
python scripts/setup_subscriptions.py
# Choose option 5 to list subscriptions
```

**View webhook server logs:**
```bash
# Server logs show incoming webhook notifications
tail -f logs/webhook_monitor.log
```

## 📚 **Additional Resources**

- [Microsoft Graph Webhooks Documentation](https://docs.microsoft.com/en-us/graph/webhooks)
- [Azure AD App Registration Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [ngrok Documentation](https://ngrok.com/docs)

## 🔐 **Security Notes**

- Keep your client secret secure and never commit it to version control
- Use HTTPS for all webhook endpoints in production
- Validate webhook notifications using clientState parameter
- Monitor for unusual subscription activity
- Regularly rotate client secrets 