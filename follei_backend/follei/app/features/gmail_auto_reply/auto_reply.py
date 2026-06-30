import time
import logging
from typing import Optional
import sys
import os

# Add current directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __package__:
    from .config import GMAIL_AUTO_REPLY_ENABLED, GMAIL_POLL_SECONDS, GMAIL_AUTO_REPLY_QUERY
    from .gmail_client import get_gmail_service, get_unread_messages, get_message_details, extract_message_data, send_reply, add_message_label
    from .reply_generator import generate_reply, generate_simple_reply
else:
    # Docker/local runner imports this file as a top-level module.
    from config import GMAIL_AUTO_REPLY_ENABLED, GMAIL_POLL_SECONDS, GMAIL_AUTO_REPLY_QUERY
    from gmail_client import get_gmail_service, get_unread_messages, get_message_details, extract_message_data, send_reply, add_message_label
    from reply_generator import generate_reply, generate_simple_reply

logger = logging.getLogger(__name__)


def is_automated_message(message: dict, from_value: str) -> bool:
    '''Return True for mailing lists, bulk mail, and no-reply senders.'''
    headers = {
        header.get('name', '').lower(): header.get('value', '').strip().lower()
        for header in message.get('payload', {}).get('headers', [])
    }
    sender = from_value.lower().replace('_', '').replace('-', '')
    blocked_sender_markers = ('noreply', 'donotreply', 'mailerdaemon')

    return (
        not from_value.strip()
        or any(marker in sender for marker in blocked_sender_markers)
        or headers.get('auto-submitted', 'no') != 'no'
        or headers.get('precedence', '') in {'bulk', 'junk', 'list'}
        or bool(headers.get('list-id'))
        or bool(headers.get('list-unsubscribe'))
    )


def process_single_message(service, message_info: dict) -> bool:
    """
    Process a single message and send an auto-reply.
    
    Args:
        service: Gmail API service instance
        message_info: Message info from list (contains id)
    
    Returns:
        True if reply was sent successfully, False otherwise
    """
    msg_id = message_info.get("id")
    if not msg_id:
        return False

    # Get full message details
    message = get_message_details(service, msg_id)
    if not message:
        return False

    # Extract message data
    msg_data = extract_message_data(message)
    if is_automated_message(message, msg_data['from']):
        sender = msg_data['from']
        logger.info(f'Skipping automated email from {sender}')
        add_message_label(service, msg_id, 'Follei-Auto-Reply-Ignored')
        return False
    logger.info(
        f"Processing message: {msg_data['subject']} from {msg_data['from']}"
    )

    # Generate reply
    reply_body = generate_reply(
        original_subject=msg_data["subject"],
        original_body=msg_data["body"],
        from_email=msg_data["from"],
    )

    # If AI generation returned fallback, use simple reply
    if reply_body == "Thank you for your email. We have received your message and will get back to you soon.":
        reply_body = generate_simple_reply(msg_data["subject"], msg_data["from"])

    # Send reply
    sent_message = send_reply(
        service=service,
        to_email=msg_data["from"],
        subject=msg_data["subject"],
        body=reply_body,
        thread_id=msg_data["thread_id"],
        message_id=msg_id,
    )

    if sent_message:
        logger.info(f"Successfully sent auto-reply to {msg_data['from']}")
        return True
    else:
        logger.error(f"Failed to send auto-reply for message {msg_id}")
        return False


def run_auto_reply_cycle(service) -> int:
    """
    Run one cycle of auto-reply processing.
    
    Args:
        service: Gmail API service instance
    
    Returns:
        Number of replies sent
    """
    if not GMAIL_AUTO_REPLY_ENABLED:
        logger.info("Auto-reply is disabled")
        return 0

    logger.info("Starting auto-reply cycle...")

    # Fetch unread messages
    messages = get_unread_messages(service, GMAIL_AUTO_REPLY_QUERY)
    logger.info(f"Found {len(messages)} unread messages to process")

    replies_sent = 0
    for message_info in messages:
        try:
            if process_single_message(service, message_info):
                replies_sent += 1
        except Exception as e:
            logger.error(f"Error processing message {message_info.get('id')}: {e}")

    logger.info(f"Auto-reply cycle completed. Sent {replies_sent} replies.")
    return replies_sent


def start_auto_reply_service():
    """
    Start the auto-reply service that runs continuously.
    This function blocks and runs in an infinite loop.
    """
    if not GMAIL_AUTO_REPLY_ENABLED:
        logger.info("Gmail auto-reply is disabled in configuration")
        return

    logger.info("Starting Gmail auto-reply service...")
    logger.info(f"Poll interval: {GMAIL_POLL_SECONDS} seconds")
    logger.info(f"Query: {GMAIL_AUTO_REPLY_QUERY}")

    # Get Gmail service
    try:
        service = get_gmail_service()
        logger.info("Gmail service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gmail service: {e}")
        return

    # Main loop
    while True:
        try:
            run_auto_reply_cycle(service)
        except Exception as e:
            logger.error(f"Error in auto-reply cycle: {e}")

        # Wait before next cycle
        logger.info(f"Waiting {GMAIL_POLL_SECONDS} seconds before next cycle...")
        time.sleep(GMAIL_POLL_SECONDS)


def run_once():
    """
    Run auto-reply once (useful for testing or manual triggers).
    """
    if not GMAIL_AUTO_REPLY_ENABLED:
        logger.info("Gmail auto-reply is disabled in configuration")
        return 0

    try:
        service = get_gmail_service()
        return run_auto_reply_cycle(service)
    except Exception as e:
        logger.error(f"Failed to run auto-reply: {e}")
        return 0
