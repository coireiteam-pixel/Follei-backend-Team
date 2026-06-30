"""
Gmail API Authorization Script

Run this script to authorize the Gmail account for the first time.
This will open a browser window for OAuth 2.0 authentication.

Usage:
    # From gmail_auto_reply folder:
    python authorize.py
    
    # From backend root:
    python -m app.features.gmail_auto_reply.authorize
"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Add parent directory to path to allow imports when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE
except ImportError:
    # When run directly (not as module)
    from config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def main():
    """Authorize Gmail API access."""
    creds = None
    token_path = GMAIL_TOKEN_FILE
    credentials_path = GMAIL_CREDENTIALS_FILE

    print("=" * 60)
    print("Gmail Auto-Reply Authorization")
    print("=" * 60)
    print()

    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"ERROR: Gmail credentials file not found at: {credentials_path}")
        print()
        print("Please follow these steps to set up Gmail API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Go to Credentials > Create Credentials > OAuth 2.0 Client ID")
        print("5. Choose 'Desktop app' as application type")
        print("6. Download the JSON file and save it as 'gmail_credentials.json'")
        print(f"   in the secrets folder: {os.path.dirname(credentials_path)}")
        print()
        sys.exit(1)

    # Check if token already exists
    if os.path.exists(token_path):
        print(f"Token file already exists at: {token_path}")
        response = input("Do you want to re-authorize? (y/N): ").strip().lower()
        if response != "y":
            print("Authorization cancelled.")
            sys.exit(0)

    # Try to load existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        print(f"Loaded existing token from: {token_path}")

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
        else:
            print("No valid credentials found. Starting OAuth flow...")
            print("A browser window will open for authentication.")
            print()
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            print()
            print("Authentication successful!")

        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        print(f"Token saved to: {token_path}")
    else:
        print("Token is valid, no need to re-authorize.")

    # Test the connection
    try:
        print()
        print("Testing Gmail API connection...")
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        print(f"✓ Successfully connected to Gmail!")
        print(f"  Email: {profile.get('emailAddress')}")
        print(f"  Messages Total: {profile.get('messagesTotal')}")
        print()
        print("Authorization complete! You can now use the auto-reply feature.")
    except Exception as e:
        print(f"✗ Error testing connection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()