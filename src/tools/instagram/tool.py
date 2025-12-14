"""
Instagram tools implementation module.
"""

import logging
from datetime import datetime
from typing import List, Optional, Iterator, Dict, Any
from pydantic import Field, BaseModel
from langchain_core.tools import tool

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_instagram_data(
    username: str,
    minutes_since: int = 30,
) -> Iterator[Dict[str, Any]]:
    """
    Fetch recent Instagram messages (DMs) for the specified username.
    
    Args:
        username: Instagram handle/username
        minutes_since: Only retrieve emails newer than this many minutes
        
    Yields:
        Dict objects containing processed message information
    """
    # Mock implementation
    logger.info(f"Fetching Instagram messages for {username} from last {minutes_since} minutes")
    
    # Mock message
    mock_msg = {
        "platform": "instagram",
        "sender": "ig_user_123",
        "recipient": username,
        "content": "Hey! Do you have availability for a collab next week?",
        "id": "ig-msg-001",
        "thread_id": "ig-thread-001",
        "timestamp": datetime.now().isoformat()
    }
    
    yield mock_msg

class FetchInstagramInput(BaseModel):
    """Input schema for fetch_instagram_messages."""
    username: str = Field(description="Instagram username to fetch messages for")
    minutes_since: int = Field(default=30, description="Only retrieve messages newer than this many minutes")

@tool(args_schema=FetchInstagramInput)
def fetch_instagram_messages(username: str, minutes_since: int = 30) -> str:
    """
    Fetches recent Direct Messages (DMs) from Instagram.
    """
    messages = list(fetch_instagram_data(username, minutes_since))
    
    if not messages:
        return "No new Instagram messages found."
    
    result = f"Found {len(messages)} new Instagram messages:\n\n"
    for i, msg in enumerate(messages, 1):
        result += f"{i}. From: {msg['sender']}\n"
        result += f"   To: {msg['recipient']}\n"
        result += f"   Time: {msg['timestamp']}\n"
        result += f"   ID: {msg['id']}\n"
        result += f"   Thread ID: {msg['thread_id']}\n"
        result += f"   Content: {msg['content']}\n\n"
        
    return result

class SendInstagramInput(BaseModel):
    """Input schema for send_instagram_message."""
    recipient: str = Field(description="Instagram username of the recipient")
    content: str = Field(description="Message content")
    
@tool(args_schema=SendInstagramInput)
def send_instagram_message(recipient: str, content: str) -> str:
    """
    Send a Direct Message (DM) to an Instagram user.
    """
    logger.info(f"Sending Instagram DM to {recipient}: {content}")
    return f"Instagram message sent successfully to {recipient}"
