#!/usr/bin/env python3
"""
Azure AD App Configuration Fix Script
====================================

This script provides step-by-step instructions to fix your Azure AD app
configuration for InboxPilot automation.

Current Issue: App is configured for personal accounts but needs organizational
account configuration for proper automation features.
"""

import os
import webbrowser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_banner():
    """Print banner"""
    print("=" * 70)
    print("🔧 InboxPilot - Azure AD App Configuration Fix")
    print("=" * 70)
    print()

def get_app_info():
    """Get app information from environment"""
    tenant_id = os.getenv("MICROSOFT_TENANT_ID")
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    
    return tenant_id, client_id

def print_current_issue():
    """Explain the current issue"""
    print("🚨 CURRENT ISSUE")
    print("-" * 20)
    print("Your Azure AD app is configured for 'Personal Microsoft accounts only'")
    print("but InboxPilot needs 'Organizational accounts' for automation features.")
    print()
    print("❌ What doesn't work:")
    print("   • Email subscriptions (/me endpoint)")
    print("   • Application permissions")
    print("   • Automated webhook subscriptions")
    print()
    print("✅ What will work after fix:")
    print("   • All email monitoring")
    print("   • Teams chat monitoring")
    print("   • Teams channel monitoring")
    print("   • Automated subscription management")
    print()

def print_fix_steps(tenant_id, client_id):
    """Print step-by-step fix instructions"""
    print("🔧 FIX INSTRUCTIONS")
    print("-" * 20)
    print()
    
    azure_portal_url = f"https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Authentication/appId/{client_id}"
    
    print("STEP 1: Open Azure Portal")
    print(f"   🌐 URL: {azure_portal_url}")
    print("   📝 This will take you directly to your app's Authentication page")
    print()
    
    print("STEP 2: Change Supported Account Types")
    print("   1. Look for 'Supported account types' section")
    print("   2. Select: 'Accounts in this organizational directory only'")
    print("   3. Click 'Save' at the top")
    print()
    
    print("STEP 3: Update API Permissions")
    permissions_url = f"https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/{client_id}"
    print(f"   🌐 URL: {permissions_url}")
    print("   1. Click 'Add a permission'")
    print("   2. Select 'Microsoft Graph'")
    print("   3. Choose 'Application permissions'")
    print("   4. Add these permissions:")
    print("      • Mail.Read")
    print("      • Chat.Read.All")
    print("      • ChannelMessage.Read.All")
    print("      • Team.ReadBasic.All")
    print("      • User.Read.All")
    print("   5. Click 'Grant admin consent for [Your Organization]'")
    print()
    
    print("STEP 4: Update Code Configuration")
    print("   After making Azure changes, update your code:")
    print("   1. The script will automatically detect the change")
    print("   2. Or restart your application")
    print()

def print_verification_steps():
    """Print verification steps"""
    print("✅ VERIFICATION")
    print("-" * 15)
    print("After making the changes:")
    print()
    print("1. Test authentication:")
    print("   python3 scripts/setup_subscriptions.py")
    print()
    print("2. You should see:")
    print("   ✅ Successfully obtained access token")
    print("   ✅ Detected user ID: [some-id]")
    print()
    print("3. Try creating email subscription (should work now)")
    print()

def open_azure_portal(client_id):
    """Open Azure portal in browser"""
    azure_url = f"https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Authentication/appId/{client_id}"
    
    try:
        print(f"🌐 Opening Azure Portal in your browser...")
        webbrowser.open(azure_url)
        print("✅ Browser opened")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"📋 Manual URL: {azure_url}")

def main():
    """Main function"""
    print_banner()
    
    tenant_id, client_id = get_app_info()
    
    if not tenant_id or not client_id:
        print("❌ Missing Azure AD app information in .env file")
        print("Please ensure MICROSOFT_TENANT_ID and MICROSOFT_CLIENT_ID are set")
        return
    
    print(f"📋 App Information:")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   Client ID: {client_id}")
    print()
    
    print_current_issue()
    print_fix_steps(tenant_id, client_id)
    print_verification_steps()
    
    # Ask if user wants to open Azure Portal
    response = input("🌐 Open Azure Portal now? (Y/n): ").strip().lower()
    if response != 'n':
        open_azure_portal(client_id)
    
    print()
    print("💡 After making these changes, run:")
    print("   python3 scripts/setup_subscriptions.py")
    print()
    print("📖 For more details, see: docs/AZURE_APP_CONFIGURATION.md")

if __name__ == "__main__":
    main() 