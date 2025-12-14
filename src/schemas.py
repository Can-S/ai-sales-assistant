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
    """Updated user preferences based on user's feedback."""
    chain_of_thought: str = Field(description="Reasoning about which user preferences need to add/update if required")
    user_preferences: str = Field(description="Updated user preferences")