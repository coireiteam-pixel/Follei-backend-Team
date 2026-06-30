import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_AUTO_REPLY_ENABLED = os.getenv("GMAIL_AUTO_REPLY_ENABLED", "false").lower() == "true"
GMAIL_POLL_SECONDS = int(os.getenv("GMAIL_POLL_SECONDS", "60"))
GMAIL_AUTO_REPLY_QUERY = os.getenv(
    "GMAIL_AUTO_REPLY_QUERY",
    "is:unread in:inbox -from:me newer_than:1d -label:Follei-Auto-Replied",
)

if '-label:Follei-Auto-Reply-Ignored' not in GMAIL_AUTO_REPLY_QUERY:
    GMAIL_AUTO_REPLY_QUERY += ' -label:Follei-Auto-Reply-Ignored'

# Handle credentials file path - support both module and direct execution
_credentials_path = os.getenv(
    "GMAIL_CREDENTIALS_FILE", "app/features/gmail_auto_reply/secrets/gmail_credentials.json"
)
_token_path = os.getenv(
    "GMAIL_TOKEN_FILE", "app/features/gmail_auto_reply/secrets/gmail_token.json"
)

# If the path doesn't exist and we're in the gmail_auto_reply folder, use local secrets/
_current_dir = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(_credentials_path) and os.path.basename(_current_dir) == "gmail_auto_reply":
    # Running from gmail_auto_reply folder directly
    GMAIL_CREDENTIALS_FILE = os.path.join(_current_dir, "secrets", "gmail_credentials.json")
    GMAIL_TOKEN_FILE = os.path.join(_current_dir, "secrets", "gmail_token.json")
else:
    # Running as module from backend root
    GMAIL_CREDENTIALS_FILE = _credentials_path
    GMAIL_TOKEN_FILE = _token_path

# The standalone Docker image mounts OAuth files at /app/secrets, while older
# .env files may still contain backend-root paths such as app/features/....
_local_secrets_dir = os.path.join(_current_dir, 'secrets')
if os.path.isdir(_local_secrets_dir):
    if not os.path.exists(GMAIL_CREDENTIALS_FILE):
        GMAIL_CREDENTIALS_FILE = os.path.join(_local_secrets_dir, 'gmail_credentials.json')
    if not os.path.exists(GMAIL_TOKEN_FILE):
        GMAIL_TOKEN_FILE = os.path.join(_local_secrets_dir, 'gmail_token.json')

GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
