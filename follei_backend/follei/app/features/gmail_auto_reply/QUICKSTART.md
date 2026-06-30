# Quick Start Guide - Gmail Auto-Reply

## Current Status
✅ .env file - READY (all keys configured)  
✅ Dependencies - INSTALLED  
✅ Code - COMPLETE  
⚠️  gmail_credentials.json - MISSING (need to add this)

## To Run: Choose Your Method

### Option A: Using Docker (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed
- `gmail_credentials.json` already in `secrets/` folder

**Steps:**

1. **Authorize first (one-time only):**
   ```bash
   # If you're NOT in the gmail_auto_reply folder:
   cd app/features/gmail_auto_reply
   
   # If you're already in the gmail_auto_reply folder, just run:
   python authorize.py
   ```
   
   **Note:** If token already exists, type `n` and press Enter to skip.
   
   (This creates `gmail_token.json` in secrets folder)

2. **Start with Docker:**
   ```bash
   docker-compose up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stop when needed:**
   ```bash
   docker-compose down
   ```

**That's it!** The container runs continuously and auto-restarts if it crashes.

### Option B: Run Locally (Without Docker)

**Step 1: Get Gmail Credentials (REQUIRED)

1. Open: https://console.cloud.google.com/
2. Create project → Enable "Gmail API"
3. Go to: Credentials → Create Credentials → OAuth 2.0 Client ID
4. Select: **Desktop app**
5. Download the JSON file
6. Rename it to: `gmail_credentials.json`
7. Place it here:
   ```
   app/features/gmail_auto_reply/secrets/gmail_credentials.json
   ```

### Step 2: Authorize

```bash
cd app/features/gmail_auto_reply
python authorize.py
```

This will:
- Open browser for Google login
- Create `gmail_token.json` automatically
- Test the connection

### Step 3: Run

```bash
# Check if setup is correct
python check_setup.py

# Run the service
python run.py
```

Then select:
- **1** = Run once (test mode)
- **2** = Continuous service (keeps running)

## That's It!

The system will now:
- Check emails every 60 seconds
- Generate AI replies using Mistral
- Send responses automatically
- Label replied emails

## Troubleshooting

**Problem**: "gmail_credentials.json not found"
**Solution**: You must download it from Google Cloud Console (Step 1 above)

**Problem**: "Token expired"
**Solution**: Delete `secrets/gmail_token.json` and run `python authorize.py` again

**Problem**: No emails being processed
**Solution**: 
- Check `.env` has `GMAIL_AUTO_REPLY_ENABLED=true`
- Send a test email to the authorized Gmail account
- Check the query in `.env` is correct

## Files in This Folder

```
gmail_auto_reply/
├── .env                    ← Your API keys (already configured)
├── secrets/                ← ADD gmail_credentials.json HERE
│   └── gmail_token.json    ← Created after authorization
├── authorize.py            ← Run this first
├── check_setup.py          ← Verify everything is ready
├── run.py                  ← Start the service
├── auto_reply.py           ← Main logic
├── gmail_client.py         ← Gmail API
├── reply_generator.py      ← AI replies
└── config.py               ← Configuration