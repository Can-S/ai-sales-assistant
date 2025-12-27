from typing import List, Any
import json
import html2text

def format_message_markdown(sender, recipient, content, subject=None, timestamp=None, platform="email", message_id=None):
    """Format message details into a nicely formatted markdown string for display
    
    Args:
        sender: Message sender
        recipient: Message recipient
        content: Message content
        subject: Optional subject (for emails)
        timestamp: Optional timestamp
        platform: Platform (gmail, instagram, whatsapp)
        message_id: Optional message ID
    """
    id_section = f"\n**ID**: {message_id}" if message_id else ""
    subject_section = f"\n**Subject**: {subject}" if subject else ""
    timestamp_section = f"\n**Timestamp**: {timestamp}" if timestamp else ""
    
    return f"""
**Platform**: {platform}{id_section}{timestamp_section}{subject_section}
**From**: {sender}
**To**: {recipient}

{content}

---
"""

def format_html_message_markdown(sender, recipient, content, subject=None, timestamp=None, platform="gmail", message_id=None):
    """Format HTML message (like Gmail) into a nicely formatted markdown string for display,
    with HTML to text conversion for HTML content
    """
    
    # Check if content is HTML and convert to text if needed
    if content and (content.strip().startswith("<!DOCTYPE") or 
                          content.strip().startswith("<html") or
                          "<body" in content):
        # Convert HTML to markdown text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0  # Don't wrap text
        content = h.handle(content)
    
    return format_message_markdown(sender, recipient, content, subject, timestamp, platform, message_id)

def format_for_display(tool_call):
    """Format content for display in Agent Inbox"""
    display = ""
    
    # Add tool call information
    if tool_call["name"] == "write_email":
        display += f"""# Email Draft

**To**: {tool_call["args"].get("to")}
**Subject**: {tool_call["args"].get("subject")}

{tool_call["args"].get("content")}
"""
    elif tool_call["name"] in ["write_message", "send_message", "respond"]:
         display += f"""# Response Draft

**To**: {tool_call["args"].get("recipient") or tool_call["args"].get("to")}
**Platform**: {tool_call["args"].get("platform", "Unknown")}

{tool_call["args"].get("content")}
"""
    elif tool_call["name"] == "schedule_meeting":
        display += f"""# Calendar Invite

**Meeting**: {tool_call["args"].get("subject")}
**Attendees**: {', '.join(tool_call["args"].get("attendees", []))}
**Duration**: {tool_call["args"].get("duration_minutes")} minutes
**Day**: {tool_call["args"].get("preferred_day")}
"""
    elif tool_call["name"] == "Question":
        display += f"""# Question for User

{tool_call["args"].get("content")}
"""
    else:
        display += f"""# Tool Call: {tool_call["name"]}

Arguments:"""
        if isinstance(tool_call["args"], dict):
            display += f"\n{json.dumps(tool_call['args'], indent=2)}\n"
        else:
            display += f"\n{tool_call['args']}\n"
    return display

def parse_message(message_input: dict) -> dict:
    """Parse a message input dictionary.

    Args:
        message_input (dict): Dictionary generic message fields.
        Supports multiple formats:
        - Generic: sender, recipient, content, subject, timestamp, platform
        - Email: author (or from), to, email_thread (or body), subject, timestamp
        - Gmail: from, to, body, subject, internalDate

    Returns:
        tuple: (sender, recipient, subject, content, timestamp, platform)
    """
    if message_input is None:
        message_input = {}
    
    # Handle different field name variations
    sender = message_input.get("sender") or message_input.get("author") or message_input.get("from")
    recipient = message_input.get("recipient") or message_input.get("to")
    content = message_input.get("content") or message_input.get("email_thread") or message_input.get("body")
    subject = message_input.get("subject")
    timestamp = message_input.get("timestamp") or message_input.get("internalDate")
    platform = message_input.get("platform", "email")
    
    return (
        sender,
        recipient,
        subject,
        content,
        timestamp,
        platform,
    )

def parse_gmail_message(message_input: dict) -> tuple:
    """Parse a Gmail input dictionary."""
    # Gmail schema mapping
    return (
        message_input.get("from"),
        message_input.get("to"),
        message_input.get("subject"),
        message_input.get("body"),
        message_input.get("internalDate"),
        "gmail",
        message_input.get("id"),
    )

def extract_message_content(message) -> str:
    """Extract content from different message types as clean string."""
    content = message.content
    
    if isinstance(content, str) and '<Recursion on AIMessage with id=' in content:
        return "[Recursive content]"
    
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                text_parts.append(item['text'])
        return "\n".join(text_parts)
    
    return str(content)

def format_few_shot_examples(examples):
    """Format examples into a readable string representation."""
    formatted = []
    for example in examples:
        val = example.value
        try:
            # Try to adapt to potential variations, but stick to the expected split
            if 'Original routing:' in val:
                message_part = val.split('Original routing:')[0].strip()
                original_routing = val.split('Original routing:')[1].split('Correct routing:')[0].strip()
                correct_routing = val.split('Correct routing:')[1].strip()
                
                formatted_example = f"""Example:
Message: {message_part}
Original Classification: {original_routing}
Correct Classification: {correct_routing}
---"""
                formatted.append(formatted_example)
            else:
                 formatted.append(f"Example:\n{val}\n---")
        except Exception:
             formatted.append(f"Example:\n{val}\n---")
    
    return "\n".join(formatted)

def extract_tool_calls(messages: List[Any]) -> List[str]:
    """Extract tool call names from messages, safely handling messages without tool_calls."""
    tool_call_names = []
    for message in messages:
        if isinstance(message, dict) and message.get("tool_calls"):
            tool_call_names.extend([call["name"].lower() for call in message["tool_calls"]])
        elif hasattr(message, "tool_calls") and message.tool_calls:
            tool_call_names.extend([call["name"].lower() for call in message.tool_calls])
    
    return tool_call_names

def format_messages_string(messages: List[Any]) -> str:
    """Format messages into a single string for analysis."""
    return '\n'.join(message.pretty_repr() for message in messages)

def show_graph(graph, xray=False):
    """Display a LangGraph mermaid diagram with fallback rendering."""
    from IPython.display import Image
    return Image(graph.get_graph(xray=xray).draw_mermaid_png())

def generate_thread_id(platform: str, sender: str) -> str:
    """Generate consistent thread_id from platform and sender.
    
    Args:
        platform: Platform name (instagram, whatsapp, email, gmail)
        sender: Sender identifier (e.g., "Sarah Chen @sarahchen_marketing" or "john@example.com")
    
    Returns:
        thread_id: Consistent identifier (e.g., "instagram_sarahchen_marketing")
    
    Examples:
        >>> generate_thread_id("instagram", "Sarah Chen @sarahchen_marketing")
        'instagram_sarahchen_marketing'
        >>> generate_thread_id("whatsapp", "John Doe")
        'whatsapp_john_doe'
    """
    if platform.lower() in ["email", "gmail"]:
        # For emails, use the full address but sanitized
        # Extract email if in "Name <email>" format
        if "<" in sender and ">" in sender:
            import re
            match = re.search(r'<([^>]+)>', sender)
            if match:
                sender = match.group(1)
        
        username = sender.strip().replace("@", "_at_").replace(".", "_")
    elif "@" in sender:
        username = sender.split("@")[-1].strip()
    else:
        username = sender.replace(" ", "_").lower()
    
    # Ensure safe characters
    username = "".join(c for c in username if c.isalnum() or c in "_-")
    
    return f"{platform}_{username}"