# Azure AD App Configuration Guide

## 🎯 **Account Types & Endpoints**

Your Azure AD app is currently configured for **Microsoft personal accounts only**. This affects how authentication works:

### **Current Configuration (Personal Accounts)**
- **Supported account types**: Personal Microsoft accounts only
- **Authentication endpoint**: `/consumers`
- **Permissions**: Delegated permissions with user consent
- **Authentication flow**: Authorization Code flow (requires user sign-in)

### **Alternative Configuration (Organizational Accounts)**
- **Supported account types**: Accounts in organizational directory
- **Authentication endpoint**: `/{tenant-id}`
- **Permissions**: Application permissions with admin consent
- **Authentication flow**: Client Credentials flow (no user sign-in)

## 🔧 **Fixing the Current Setup**

### **Option 1: Change to Organizational Accounts (Recommended)**

1. **Go to Azure Portal** → App registrations → Your app
2. **Authentication** → Supported account types
3. **Select**: "Accounts in this organizational directory only"
4. **Save** the changes
5. **API Permissions** → Add application permissions:
   - `Mail.Read` (Microsoft Graph)
   - `Chat.Read.All` (Microsoft Graph)
   - `ChannelMessage.Read.All` (Microsoft Graph)
   - `Team.ReadBasic.All` (Microsoft Graph)
6. **Grant admin consent** for the permissions

### **Option 2: Use Personal Account Flow (Current Setup)**

For personal accounts, you need user authentication. Update your code to use:

```python
# Use authorization code flow for personal accounts
auth_url = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
token_url = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/token"

# Required scopes for personal accounts
scopes = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Chat.Read", 
    "https://graph.microsoft.com/ChannelMessage.Read",
    "offline_access"
]
```

## 🚀 **Quick Fix Instructions**

### **Step 1: Change Account Type**
```bash
# Go to Azure Portal
# Navigate to: Azure Active Directory → App registrations → [Your App]
# Click: Authentication → Supported account types
# Select: "Accounts in this organizational directory only"
# Save changes
```

### **Step 2: Update Permissions**
```bash
# In your app registration:
# Go to: API permissions
# Remove existing permissions
# Add Application permissions:
#   - Microsoft Graph → Mail.Read
#   - Microsoft Graph → Chat.Read.All  
#   - Microsoft Graph → ChannelMessage.Read.All
#   - Microsoft Graph → Team.ReadBasic.All
# Click: "Grant admin consent for [Organization]"
```

### **Step 3: Update Environment Variables**
```bash
# In your .env file, keep the same values:
MICROSOFT_TENANT_ID=your_tenant_id_here
MICROSOFT_CLIENT_ID=your_client_id_here
MICROSOFT_CLIENT_SECRET=your_client_secret_here
```

### **Step 4: Update Code Endpoints**
After changing to organizational accounts, update the token URL back to:
```python
self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
```

## 🔍 **Verification Steps**

After making changes:

1. **Test authentication**:
   ```bash
   python3 scripts/setup_subscriptions.py
   ```

2. **Check permissions**:
   - Should see "✅ Successfully obtained access token"
   - No more "AADSTS9002346" errors

3. **Create subscriptions**:
   - Email monitoring should work
   - Teams monitoring should work (if permissions are correct)

## 📚 **Understanding the Error**

**Error**: `AADSTS9002346: Application is configured for use by Microsoft Account users only`

**Cause**: Your app is set for personal accounts but you're trying to use organizational authentication endpoints.

**Solutions**:
- **Best**: Change app to organizational accounts (enables automation)
- **Alternative**: Implement user authentication flow for personal accounts

## 🔐 **Security Considerations**

### **Organizational Accounts (Recommended)**
- ✅ Supports application permissions (no user interaction)
- ✅ Better for automation and webhooks
- ✅ Admin can control access
- ❌ Requires organizational Azure AD

### **Personal Accounts**
- ✅ Works with personal Microsoft accounts
- ✅ No organizational setup required
- ❌ Requires user sign-in for each session
- ❌ Limited automation capabilities
- ❌ Cannot use application permissions

For InboxPilot's automation features, **organizational accounts** are strongly recommended. 