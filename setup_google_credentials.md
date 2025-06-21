# Google Cloud Credentials Setup Guide

## 📧 Setting up Gmail API Access

Follow these steps to get your `credentials.json` file:

### 1. **Google Cloud Console Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. **Create OAuth 2.0 Credentials**
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Give it a name (e.g., "InboxPilot Gmail Access")
5. Click "Create"

### 3. **Download Credentials**
1. Click the download button (⬇️) next to your new OAuth client
2. Save the file as `credentials.json` in your InboxPilot directory
3. Keep this file secure and never commit it to version control

### 4. **OAuth Consent Screen** (if required)
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" for testing
3. Fill in required fields:
   - App name: "InboxPilot"
   - User support email: your email
   - Developer contact: your email
4. Add your email to test users

### 5. **File Placement**
Place the `credentials.json` file in your project root:
```
InboxPilot/
├── credentials.json  ← Place here
├── mcp_server/
├── chromadb_data/
└── ...
```

### 6. **Test the Setup**
```bash
source venv311/bin/activate
python mcp_server/gmail_server.py
```

## 🔒 **Security Notes**
- Add `credentials.json` to `.gitignore`
- Never share this file publicly
- Rotate credentials if compromised
- Use service accounts for production 