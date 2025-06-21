# Gmail Setup Guide

## Issue: Access Blocked - Gmail App Not Verified

The error you're encountering happens because the Gmail application hasn't completed Google's verification process. Here are the solutions:

## Solution 1: Create Your Own Google Cloud Project (Recommended)

### Step 1: Set Up Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

### Step 2: Enable Gmail API
1. Navigate to "APIs & Services" > "Library"
2. Search for "Gmail API" 
3. Click on it and press "Enable"

### Step 3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - User Type: "External" (for personal Gmail) or "Internal" (for G Workspace)
   - App name: "InboxPilot Gmail Client"
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add Gmail scopes if prompted
4. Application type: "Desktop application"
5. Name: "InboxPilot Gmail Client"
6. Click "Create"

### Step 4: Download Credentials
1. Click the download button next to your newly created OAuth client
2. Save the file as `credentials.json` in the `mcp_server/` directory
3. The file should look like this:

```json
{
  "installed": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

### Step 5: Test the Setup
1. Run your test script again:
   ```bash
   cd mcp_server
   python test_gmail.py
   ```
2. You should see a new OAuth flow with your own app

## Solution 2: Configure OAuth Consent Screen for Testing

If you want to use the existing app but add test users:

### For the App Owner
1. Go to Google Cloud Console for the project
2. Navigate to "APIs & Services" > "OAuth consent screen"
3. Add `liu.tony1025@gmail.com` to "Test users"
4. Save the changes

### For You (if you're not the app owner)
Contact the app developer to add your email as a test user.

## Solution 3: Use a Service Account (For Production)

For production use without user interaction:

1. Create a Service Account in Google Cloud Console
2. Download the service account key JSON
3. Modify the Gmail server to use service account authentication
4. Enable domain-wide delegation if needed

## Next Steps

After setting up your own credentials:

1. Delete any existing `token.json` file in `mcp_server/`
2. Run the test script: `python test_gmail.py`
3. Complete the OAuth flow in your browser
4. The app should work with your own Google Cloud project

## Security Notes

- Keep your `credentials.json` file secure and never commit it to version control
- The file is already in `.gitignore` to prevent accidental commits
- For production, consider using service accounts or more secure authentication methods

## Troubleshooting

- **Invalid client error**: Check that Gmail API is enabled in your project
- **Redirect URI mismatch**: Ensure your OAuth client is configured as "Desktop application"
- **Scope errors**: Verify that your consent screen includes the required Gmail scopes 