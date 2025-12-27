from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal
from langgraph.graph import MessagesState

class RouterSchema(BaseModel):
    """Analyze the unread message and route it according to its content."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of a message: 'ignore' for irrelevant messages, "
        "'notify' for important information that doesn't need a response, "
        "'respond' for messages that need a reply",
    )

class StateInput(TypedDict):
    # This is the input to the state
    message_input: dict

class State(MessagesState):
    # This state class has the messages key build in
    message_input: dict
    classification_decision: Literal["ignore", "respond", "notify"]
    thread_id: str  # Track user conversations


class MessageData(TypedDict):
    id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str | None # Optional, mostly for emails
    content: str
    timestamp: str
    platform: Literal["gmail", "instagram", "whatsapp"]

class UserPreferences(BaseModel):
    """User-specific preferences and learned behaviors."""
    
    # User identification
    platform: str
    username: str
    
    # Communication preferences
    preferred_response_style: str | None = None  # e.g., "formal", "casual", "detailed"
    preferred_language: str = "en"
    
    # Business context
    company_size: int | None = None
    industry: str | None = None
    
    # Interaction history
    total_messages: int = 0
    last_interaction: str | None = None
    
    # HITL feedback patterns
    common_edits: list[str] = []  # Track what user commonly edits
    ignored_suggestions: list[str] = []  # Track what user ignores