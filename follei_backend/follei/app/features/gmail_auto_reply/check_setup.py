"""
Setup verification script for Gmail Auto-Reply
Run this to check if everything is configured correctly
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Gmail Auto-Reply Setup Checker")
print("=" * 60)
print()

errors = []
warnings = []
success = []

# Check 1: .env file
print("1. Checking .env file...")
if os.path.exists(".env"):
    success.append("✓ .env file exists")
    from config import (
        GMAIL_AUTO_REPLY_ENABLED,
        GMAIL_POLL_SECONDS,
        MISTRAL_API_KEY,
        GMAIL_CREDENTIALS_FILE,
        GMAIL_TOKEN_FILE,
    )
    
    if GMAIL_AUTO_REPLY_ENABLED:
        success.append("✓ Auto-reply is enabled")
    else:
        errors.append("✗ Auto-reply is disabled (set GMAIL_AUTO_REPLY_ENABLED=true)")
    
    if MISTRAL_API_KEY:
        success.append("✓ Mistral API key is configured")
    else:
        warnings.append("⚠ Mistral API key not set (will use template replies)")
        
else:
    errors.append("✗ .env file not found")

# Check 2: secrets folder
print("\n2. Checking secrets folder...")
if os.path.exists("secrets"):
    success.append("✓ secrets folder exists")
    
    # Check credentials file
    if os.path.exists("secrets/gmail_credentials.json"):
        success.append("✓ gmail_credentials.json exists")
    else:
        errors.append("✗ gmail_credentials.json NOT found in secrets/")
        errors.append("  → Download from Google Cloud Console (see README)")
    
    # Check token file
    if os.path.exists("secrets/gmail_token.json"):
        success.append("✓ gmail_token.json exists (already authorized)")
    else:
        warnings.append("⚠ gmail_token.json not found (need to run authorization)")
else:
    errors.append("✗ secrets folder not found")
    errors.append("  → Create folder: mkdir secrets")

# Check 3: Dependencies
print("\n3. Checking Python dependencies...")
try:
    import google.auth
    import googleapiclient
    import requests
    import dotenv
    success.append("✓ All required packages installed")
except ImportError as e:
    errors.append(f"✗ Missing package: {e}")
    errors.append("  → Run: pip install -r requirements.txt")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if success:
    print("\n✓ Success:")
    for s in success:
        print(f"  {s}")

if warnings:
    print("\n⚠ Warnings:")
    for w in warnings:
        print(f"  {w}")

if errors:
    print("\n✗ Errors:")
    for e in errors:
        print(f"  {e}")
    print("\n❌ Setup incomplete. Please fix the errors above.")
    sys.exit(1)
else:
    print("\n✅ Setup complete! You can now run the auto-reply service.")
    print("\nNext steps:")
    print("  1. Run authorization: python authorize.py")
    print("  2. Start service: python run.py")
    sys.exit(0)