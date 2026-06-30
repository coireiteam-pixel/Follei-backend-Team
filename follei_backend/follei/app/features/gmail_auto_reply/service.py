'''Non-interactive entry point for the Docker Gmail auto-reply worker.'''

import logging

from auto_reply import start_auto_reply_service
from config import GMAIL_AUTO_REPLY_ENABLED


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)

if not GMAIL_AUTO_REPLY_ENABLED:
    raise SystemExit('GMAIL_AUTO_REPLY_ENABLED must be true')

start_auto_reply_service()
