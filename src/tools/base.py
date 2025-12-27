from typing import Dict, List, Callable, Any, Optional
from langchain_core.tools import BaseTool

def get_tools(tool_names: Optional[List[str]] = None, include_gmail: bool = False, include_instagram: bool = False, include_whatsapp: bool = False) -> List[BaseTool]:
    """Get specified tools or all tools if tool_names is None.
    
    Args:
        tool_names: Optional list of tool names to include. If None, returns all tools.
        include_gmail: Whether to include Gmail tools. Defaults to False.
        include_instagram: Whether to include Instagram tools. Defaults to False.
        include_whatsapp: Whether to include WhatsApp tools. Defaults to False.
        
    Returns:
        List of tool objects
    """
    # Import default tools (using relative imports to match local structure if needed, or absolute)
    # Based on existing structure, it seems to assume `email_assistant` was the package name.
    # We should update imports to match the current directory structure if possible, 
    # but for now we stick to what seems to be the pattern or fix the package name assumption.
    # The previous file had `from email_assistant.tools...`. 
    # Since we are in `d:\LangGraph\agent\src\tools`, we should use `src.tools` or relative imports.
    
    from src.tools.default.email_tools import write_email, Done, Question
    from src.tools.default.calendar_tools import schedule_meeting, check_calendar_availability
    
    # Base tools dictionary
    all_tools = {
        "write_message": write_email, 
        "write_email": write_email, # Kept for backward compatibility if needed
        "Done": Done,
        "Question": Question,
        "schedule_meeting": schedule_meeting,
        "check_calendar_availability": check_calendar_availability,
    }
    
    # Add Gmail tools if requested
    if include_gmail:
        try:
            from src.tools.gmail.gmail_tools import (
                fetch_emails_tool,
                send_email_tool,
                check_calendar_tool,
                write_gmail_email
            )
            
            all_tools.update({
                "fetch_emails_tool": fetch_emails_tool,
                "send_email_tool": send_email_tool,
                "check_calendar_tool": check_calendar_tool,
                "write_message": write_gmail_email, # Override write_message with Gmail implementation
            })
        except ImportError:
            pass

    # Add Instagram tools
    if include_instagram:
        try:
            from src.tools.instagram.tool import fetch_instagram_messages, send_instagram_message
            all_tools.update({
                "fetch_instagram_messages": fetch_instagram_messages,
                "send_instagram_message": send_instagram_message,
            })
        except ImportError:
            pass
            
    # Add WhatsApp tools
    if include_whatsapp:
        try:
            from src.tools.whatsapp.tool import fetch_whatsapp_messages, send_whatsapp_message
            all_tools.update({
                "fetch_whatsapp_messages": fetch_whatsapp_messages,
                "send_whatsapp_message": send_whatsapp_message,
            })
        except ImportError:
            pass
    
    if tool_names is None:
        return list(all_tools.values())
    
    return [all_tools[name] for name in tool_names if name in all_tools]

def get_tools_by_name(tools: Optional[List[BaseTool]] = None) -> Dict[str, BaseTool]:
    """Get a dictionary of tools mapped by name."""
    if tools is None:
        tools = get_tools()
    
    return {tool.name: tool for tool in tools}

