"""
WhatsApp tools implementation module.
"""

import logging
from datetime import datetime
from typing import List, Optional, Iterator, Dict, Any
from pydantic import Field, BaseModel
from langchain_core.tools import tool

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_whatsapp_data(
    phone_number: str,
    minutes_since: int = 30,
) -> Iterator[Dict[str, Any]]:
    """
    Fetch recent WhatsApp messages.
    
    Args:
        phone_number: Phone number to fetch messages for
        minutes_since: Only retrieve messages newer than this many minutes
        
    Yields:
        Dict objects containing processed message information
    """
    # Mock implementation
    logger.info(f"Fetching WhatsApp messages for {phone_number} from last {minutes_since} minutes")
    
    # Mock message
    mock_msg = {
        "platform": "whatsapp",
        "sender": "+15550123456",
        "recipient": phone_number,
        "content": "Can we schedule the demo call for tomorrow at 2pm?",
        "id": "wa-msg-001",
        "thread_id": "wa-thread-001",
        "timestamp": datetime.now().isoformat()
    }
    
    yield mock_msg

class FetchWhatsAppInput(BaseModel):
    """Input schema for fetch_whatsapp_messages."""
    phone_number: str = Field(description="WhatsApp phone number to fetch messages for")
    minutes_since: int = Field(default=30, description="Only retrieve messages newer than this many minutes")

@tool(args_schema=FetchWhatsAppInput)
def fetch_whatsapp_messages(phone_number: str, minutes_since: int = 30) -> str:
    """
    Fetches recent messages from WhatsApp.
    """
    messages = list(fetch_whatsapp_data(phone_number, minutes_since))
    
    if not messages:
        return "No new WhatsApp messages found."
    
    result = f"Found {len(messages)} new WhatsApp messages:\n\n"
    for i, msg in enumerate(messages, 1):
        result += f"{i}. From: {msg['sender']}\n"
        result += f"   To: {msg['recipient']}\n"
        result += f"   Time: {msg['timestamp']}\n"
        result += f"   ID: {msg['id']}\n"
        result += f"   Thread ID: {msg['thread_id']}\n"
        result += f"   Content: {msg['content']}\n\n"
        
    return result

class SendWhatsAppInput(BaseModel):
    """Input schema for send_whatsapp_message."""
    recipient: str = Field(description="Phone number of the recipient")
    content: str = Field(description="Message content")
    
@tool(args_schema=SendWhatsAppInput)
def send_whatsapp_message(recipient: str, content: str) -> str:
    """
    Send a WhatsApp message.
    """
    logger.info(f"Sending WhatsApp message to {recipient}: {content}")
    return f"WhatsApp message sent successfully to {recipient}"
