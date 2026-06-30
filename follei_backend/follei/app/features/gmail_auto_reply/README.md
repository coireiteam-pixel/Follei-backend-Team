# Gmail Auto Reply

This feature automatically monitors a Gmail inbox, generates intelligent replies using Mistral AI, and sends threaded responses when new emails arrive.

## Features

- **Automatic Email Monitoring**: Polls Gmail inbox for unread messages
- **AI-Powered Replies**: Uses Mistral AI to generate contextual, professional responses
- **Threaded Responses**: Maintains email conversation threads
- **Smart Labeling**: Automatically labels replied emails to avoid duplicate responses
- **Configurable**: Easy to customize via environment variables

## File Structure

```
gmail_auto_reply/
├── __init__.py              # Package initialization
├── config.py                # Configuration and environment variables
├── gmail_client.py          # Gmail API integration (auth, fetch, send)
├── reply_generator.py       # AI reply generation using Mistral
├── auto_reply.py            # Main auto-reply logic and service
├── authorize.py             # OAuth authorization script
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── .env                    # Environment variables (not in git)
└── secrets/                 # Gmail credentials (not in git)
    ├── gmail_credentials.json  # OAuth 2.0 credentials from Google
    └── gmail_token.json        # Access token (auto-generated)
```

## Prerequisites

1. **Python 3.8+** installed
2. **Gmail API credentials** from Google Cloud Console
3. **Mistral API key** (optional, for AI-powered replies)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop app" as application type
   - Download the JSON file
5. Rename the downloaded file to `gmail_credentials.json`
6. Place it in the `secrets/` folder:
   ```
   gmail_auto_reply/secrets/gmail_credentials.json
   ```

**Important:** The `secrets/` folder should contain:
- `gmail_credentials.json` (downloaded from Google Cloud Console)
- `gmail_token.json` (will be auto-generated after authorization)

**Note:** Both files are in `.gitignore` and will NOT be committed to git.

### 3. Configure Environment Variables

The `.env` file in this folder contains all configuration:

```env
# Enable/disable auto-reply feature
GMAIL_AUTO_REPLY_ENABLED=true

# How often to check for new emails (in seconds)
GMAIL_POLL_SECONDS=60

# Gmail search query to find emails to reply to
GMAIL_AUTO_REPLY_QUERY=is:unread in:inbox -from:me newer_than:1d -label:Follei-Auto-Replied

# Path to Gmail credentials (relative to project root)
GMAIL_CREDENTIALS_FILE=app/features/gmail_auto_reply/secrets/gmail_credentials.json

# Path to Gmail token (auto-generated after authorization)
GMAIL_TOKEN_FILE=app/features/gmail_auto_reply/secrets/gmail_token.json

# Mistral AI API key (for AI-powered replies)
MISTRAL_API_KEY=your_mistral_api_key_here

# Mistral model to use
MISTRAL_MODEL=mistral-small-latest

# Public base URL (for webhooks if needed)
PUBLIC_BASE_URL=https://your-domain.com
```

### 4. Authorize Gmail Access

Run the authorization script to authenticate with Gmail:

**Option 1: From the gmail_auto_reply folder (Recommended)**
```bash
# Navigate to the gmail_auto_reply folder
cd app/features/gmail_auto_reply

# Run the authorization script
python authorize.py
```

**Option 2: From the backend root directory**
```bash
# From the backend root (where 'app' folder is located)
python -m app.features.gmail_auto_reply.authorize
```

This will:
- Open a browser window for Google OAuth authentication
- Ask you to log in with the Gmail account you want to monitor
- Save the access token to `secrets/gmail_token.json`
- Test the connection and display your email address

### 5. (Optional) Get Mistral API Key

For AI-powered replies:

1. Go to [Mistral AI Console](https://console.mistral.ai/)
2. Sign up and get your API key
3. Add it to the `.env` file:
   ```env
   MISTRAL_API_KEY=your_api_key_here
   ```

Without Mistral API key, the system will use simple template-based replies.

## Usage

### Start the Auto-Reply Service

The service can be started in two ways:

#### Option 1: Continuous Service (Recommended for Production)

```python
from app.features.gmail_auto_reply.auto_reply import start_auto_reply_service

# This runs continuously, checking for new emails every GMAIL_POLL_SECONDS
start_auto_reply_service()
```

#### Option 2: Run Once (For Testing)

```python
from app.features.gmail_auto_reply.auto_reply import run_once

# Process emails once and exit
replies_sent = run_once()
print(f"Sent {replies_sent} replies")
```

#### Option 3: Manual Trigger

```python
from app.features.gmail_auto_reply.auto_reply import run_auto_reply_cycle
from app.features.gmail_auto_reply.gmail_client import get_gmail_service

# Get Gmail service
service = get_gmail_service()

# Run one cycle
replies_sent = run_auto_reply_cycle(service)
```

### Integration with FastAPI/Backend

Example integration in your FastAPI app:

```python
from fastapi import FastAPI
import threading
from app.features.gmail_auto_reply.auto_reply import start_auto_reply_service

app = FastAPI()

@app.on_event("startup")
def startup_event():
    """Start auto-reply service when app starts."""
    if GMAIL_AUTO_REPLY_ENABLED:
        # Run in background thread
        thread = threading.Thread(target=start_auto_reply_service, daemon=True)
        thread.start()
```

## How It Works

1. **Polling**: The service checks Gmail inbox at configured intervals (default: 60 seconds)
2. **Filtering**: Uses Gmail search query to find unread emails that haven't been replied to
3. **Processing**: For each matching email:
   - Extracts subject, sender, and message body
   - Generates a contextual reply using Mistral AI (or template if AI unavailable)
   - Sends the reply as a threaded response
   - Adds "Follei-Auto-Replied" label to prevent duplicate replies
4. **Logging**: All actions are logged for monitoring and debugging

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `GMAIL_AUTO_REPLY_ENABLED` | Enable/disable the feature | `false` |
| `GMAIL_POLL_SECONDS` | Polling interval in seconds | `60` |
| `GMAIL_AUTO_REPLY_QUERY` | Gmail search query | `is:unread in:inbox -from:me newer_than:1d -label:Follei-Auto-Replied` |
| `GMAIL_CREDENTIALS_FILE` | Path to OAuth credentials | `app/features/gmail_auto_reply/secrets/gmail_credentials.json` |
| `GMAIL_TOKEN_FILE` | Path to access token | `app/features/gmail_auto_reply/secrets/gmail_token.json` |
| `MISTRAL_API_KEY` | Mistral AI API key | - |
| `MISTRAL_MODEL` | Mistral model name | `mistral-small-latest` |

## Gmail Query Syntax

The default query filters emails:
- `is:unread` - Only unread emails
- `in:inbox` - Only in inbox
- `-from:me` - Exclude emails sent by you
- `newer_than:1d` - Only emails from last 24 hours
- `-label:Follei-Auto-Replied` - Exclude already replied emails

Customize the query in `.env` to match your needs.

## Security Notes

- **Never commit** `secrets/` folder or `.env` file to version control
- The `.gitignore` file is configured to exclude these files
- OAuth tokens are stored locally and encrypted by Google
- Use environment variables for all sensitive configuration

## Troubleshooting

### Authorization Issues

**Problem**: "Credentials file not found"
- **Solution**: Download OAuth credentials from Google Cloud Console and place in `secrets/gmail_credentials.json`

**Problem**: "Token expired"
- **Solution**: Delete `secrets/gmail_token.json` and re-run authorization script

### API Errors

**Problem**: "Gmail API quota exceeded"
- **Solution**: Gmail API has daily quotas. Check [Google Cloud Console](https://console.cloud.google.com/) for usage limits

**Problem**: "Mistral API error"
- **Solution**: Verify your Mistral API key is correct and has available credits

### No Emails Being Processed

**Problem**: Service runs but no replies sent
- **Solution**: Check the Gmail query in `.env` - it might be too restrictive
- **Solution**: Verify `GMAIL_AUTO_REPLY_ENABLED=true` in `.env`
- **Solution**: Check logs for errors

## Logging

The service uses Python's logging module. Configure logging in your application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Testing

Test the authorization:
```bash
python -m app.features.gmail_auto_reply.authorize
```

Test a single cycle:
```python
from app.features.gmail_auto_reply.auto_reply import run_once
run_once()
```

## Running the Service

### Method 1: Using Docker (Recommended for Production)

**Prerequisites:**
- Docker and Docker Compose installed
- `gmail_credentials.json` in `secrets/` folder

**Steps:**

1. **Build and start the container:**
   ```bash
   cd app/features/gmail_auto_reply
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop the service:**
   ```bash
   docker-compose down
   ```

4. **Restart after changes:**
   ```bash
   docker-compose restart
   ```

**Note:** The container runs continuously and auto-restarts on failure.

### Method 2: Using the Runner Script (Easiest - Local)

```bash
# Navigate to the gmail_auto_reply folder
cd app/features/gmail_auto_reply

# Run the interactive runner
python run.py
```

This will show you options to run once or start continuous service.

### Method 3: Direct Python Command

```bash
# Run once (test mode)
python -c "from auto_reply import run_once; print(f'Sent {run_once()} replies')"

# Start continuous service
python -c "from auto_reply import start_auto_reply_service; start_auto_reply_service()"
```

### Method 4: Integration in Your App

```python
# In your main app file (e.g., main.py)
import threading
from app.features.gmail_auto_reply.auto_reply import start_auto_reply_service
from app.features.gmail_auto_reply.config import GMAIL_AUTO_REPLY_ENABLED

# Start on app startup
if GMAIL_AUTO_REPLY_ENABLED:
    thread = threading.Thread(target=start_auto_reply_service, daemon=True)
    thread.start()
```

### Method 5: Manual Trigger via API (if you have FastAPI)

```python
from fastapi import APIRouter
from app.features.gmail_auto_reply.auto_reply import run_once

router = APIRouter()

@router.post("/gmail/run-once")
def trigger_auto_reply():
    replies = run_once()
    return {"status": "success", "replies_sent": replies}
```

## Dependencies

- `google-api-python-client` - Gmail API client
- `google-auth-oauthlib` - OAuth 2.0 authentication
- `google-auth-httplib2` - HTTP transport for Google auth
- `requests` - HTTP client for Mistral API
- `python-dotenv` - Environment variable management

## License

Part of the Follei Backend Team project.

## Support

For issues or questions, contact the development team or check the main project repository.