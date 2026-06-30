"""
Example script to run Gmail Auto-Reply

This demonstrates different ways to use the auto-reply feature.
"""

import sys
import os

# Add project root to path
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    ),
)

from app.features.gmail_auto_reply.auto_reply import run_once, start_auto_reply_service
from app.features.gmail_auto_reply.config import GMAIL_AUTO_REPLY_ENABLED

print("=" * 60)
print("Gmail Auto-Reply Runner")
print("=" * 60)
print()

if not GMAIL_AUTO_REPLY_ENABLED:
    print("ERROR: GMAIL_AUTO_REPLY_ENABLED is not set to true in .env file")
    print("Please set GMAIL_AUTO_REPLY_ENABLED=true in your .env file")
    sys.exit(1)

print("Choose an option:")
print("1. Run once (process emails once and exit)")
print("2. Start continuous service (keeps running)")
print()

choice = input("Enter your choice (1 or 2): ").strip()

if choice == "1":
    print("\nRunning auto-reply once...")
    print("-" * 60)
    replies_sent = run_once()
    print("-" * 60)
    print(f"\nCompleted! Sent {replies_sent} replies.")
    
elif choice == "2":
    print("\nStarting continuous service...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    try:
        start_auto_reply_service()
    except KeyboardInterrupt:
        print("\n\nService stopped by user.")
        
else:
    print("Invalid choice. Please run again and select 1 or 2.")
    sys.exit(1)
