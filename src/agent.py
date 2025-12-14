
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage   

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

import os
from dotenv import load_dotenv

from src.prompts import triage_system_prompt, triage_user_prompt, agent_system_prompt_hitl, default_background, default_triage_instructions, default_response_preferences, default_cal_preferences
from src.schemas import State, RouterSchema, StateInput
from src.utils import parse_message, format_for_display, format_message_markdown
from src.tools import get_tools, get_tools_by_name
from src.tools.default.prompt_templates import HITL_TOOLS_PROMPT

load_dotenv(".env")

# Enable Instagram and WhatsApp tools
tools = get_tools(
    tool_names=[
        "write_message", 
        "schedule_meeting", 
        "check_calendar_availability", 
        "Question", 
        "Done",
        "fetch_instagram_messages",
        "send_instagram_message",
        "fetch_whatsapp_messages",
        "send_whatsapp_message"
    ],
    include_instagram=True,
    include_whatsapp=True
)
tools_by_name = get_tools_by_name(tools)

llm="gemini-2.5-flash"

model = ChatGoogleGenerativeAI(
    model=llm,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Initialize the LLM for use with router / structured output
llm_router = model.with_structured_output(RouterSchema) 

# Initialize the LLM, enforcing tool use (of any available tools) for agent
llm_with_tools = model.bind_tools(tools, tool_choice="required")

def triage_router(state: State) -> Command[Literal["triage_interrupt_handler", "response_agent", "__end__"]]:
    """Analyze message content to decide if we should respond, notify, or ignore.

    The triage step prevents the assistant from wasting time on:
    - Spam and promotions
    - Generic notifications
    - Irrelevant social media interactions
    """

    # Parse the message input (generic for email, instagram, whatsapp)
    sender, recipient, subject, content, timestamp, platform = parse_message(state["message_input"])
    
    user_prompt = triage_user_prompt.format(
        platform=platform,
        sender=sender, 
        recipient=recipient, 
        subject=subject or "N/A", 
        timestamp=timestamp, 
        content=content
    )

    # Create message markdown for Agent Inbox in case of notification  
    message_markdown = format_message_markdown(
        sender=sender, 
        recipient=recipient, 
        content=content, 
        subject=subject, 
        timestamp=timestamp, 
        platform=platform
    )

    # Format system prompt with background and triage instructions
    system_prompt = triage_system_prompt.format(
        background=default_background,
        triage_instructions=default_triage_instructions
    )

    # Run the router LLM
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    # Decision
    classification = result.classification
    print(f"Reasoning: {result.reasoning}")

    # Process the classification decision
    if classification == "respond":
        print(f"[RESPOND] Classification: RESPOND - This {platform} message requires a response")
        # Next node
        goto = "response_agent"
        # Update the state
        update = {
            "classification_decision": result.classification,
            "messages": [{"role": "user",
                            "content": f"Respond to the message: {message_markdown}"
                        }],
        }
    elif classification == "ignore":
        print(f"[IGNORE] Classification: IGNORE - This {platform} message can be safely ignored")

        # Next node
        goto = END
        # Update the state
        update = {
            "classification_decision": classification,
        }

    elif classification == "notify":
        print(f"[NOTIFY] Classification: NOTIFY - This {platform} message contains important information") 

        # Next node
        goto = "triage_interrupt_handler"
        # Update the state
        update = {
            "classification_decision": classification,
        }

    else:
        raise ValueError(f"Invalid classification: {classification}")
    return Command(goto=goto, update=update)

def triage_interrupt_handler(state: State) -> Command[Literal["response_agent", "__end__"]]:
    """Handles interrupts from the triage step"""
    
    # Parse the message input
    sender, recipient, subject, content, timestamp, platform = parse_message(state["message_input"])

    # Create message markdown for Agent Inbox in case of notification  
    message_markdown = format_message_markdown(
        sender=sender, 
        recipient=recipient, 
        content=content, 
        subject=subject, 
        timestamp=timestamp, 
        platform=platform
    )

    # Create messages
    messages = [{"role": "user",
                "content": f"Message to notify user about: {message_markdown}"
                }]

    # Create interrupt for Agent Inbox
    request = {
        "action_request": {
            "action": f"{platform.capitalize()} Assistant: {state['classification_decision']}",
            "args": {}
        },
        "config": {
            "allow_ignore": True,  
            "allow_respond": True, 
            "allow_edit": False, 
            "allow_accept": False,  
        },
        # Message to show in Agent Inbox
        "description": message_markdown,
    }

    # Agent Inbox responds with a list  
    response = interrupt([request])[0]

    # If user provides feedback, go to response agent and use feedback to respond to message   
    if response["type"] == "response":
        # Add feedback to messages 
        user_input = response["args"]
        # Used by the response agent
        messages.append({"role": "user",
                        "content": f"User wants to reply to the message. Use this feedback to respond: {user_input}"
                        })
        # Go to response agent
        goto = "response_agent"

    # If user ignores message, go to END
    elif response["type"] == "ignore":
        goto = END

    # Catch all other responses
    else:
        raise ValueError(f"Invalid response: {response}")

    # Update the state 
    update = {
        "messages": messages,
    }

    return Command(goto=goto, update=update)

def llm_call(state: State):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            llm_with_tools.invoke(
                [
                    {"role": "system", "content": agent_system_prompt_hitl.format(
                        tools_prompt=HITL_TOOLS_PROMPT,
                        background=default_background,
                        response_preferences=default_response_preferences, 
                        cal_preferences=default_cal_preferences
                    )}
                ]
                + state["messages"]
            )
        ]
    }

def interrupt_handler(state: State) -> Command[Literal["llm_call", "__end__"]]:
    """Creates an interrupt for human review of tool calls"""
    
    # Store messages
    result = []

    # Go to the LLM call node next
    goto = "llm_call"

    # Iterate over the tool calls in the last message
    for tool_call in state["messages"][-1].tool_calls:
        
        # Allowed tools for HITL
        hitl_tools = [
            "write_message", 
            "send_instagram_message", 
            "send_whatsapp_message", 
            "schedule_meeting", 
            "Question"
        ]
        
        # If tool is not in our HITL list, execute it directly without interruption
        if tool_call["name"] not in hitl_tools:

            # Execute search_memory and other tools without interruption
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
            continue
            
        # Get original message from message_input in state
        sender, recipient, subject, content, timestamp, platform = parse_message(state["message_input"])
        original_message_markdown = format_message_markdown(sender, recipient, content, subject, timestamp, platform)
        
        # Format tool call for display and prepend the original message
        tool_display = format_for_display(tool_call)
        description = original_message_markdown + tool_display

        # Configure what actions are allowed in Agent Inbox
        if tool_call["name"] in ["write_message", "send_instagram_message", "send_whatsapp_message", "schedule_meeting"]:
            config = {
                "allow_ignore": True,
                "allow_respond": True,
                "allow_edit": True,
                "allow_accept": True,
            }
        elif tool_call["name"] == "Question":
            config = {
                "allow_ignore": True,
                "allow_respond": True,
                "allow_edit": False,
                "allow_accept": False,
            }
        else:
            raise ValueError(f"Invalid tool call: {tool_call['name']}")

        # Create the interrupt request
        request = {
            "action_request": {
                "action": tool_call["name"],
                "args": tool_call["args"]
            },
            "config": config,
            "description": description,
        }

        # Send to Agent Inbox and wait for response
        response = interrupt([request])[0]

        # Handle the responses 
        if response["type"] == "accept":

            # Execute the tool with original args
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
                        
        elif response["type"] == "edit":

            # Tool selection 
            tool = tools_by_name[tool_call["name"]]
            
            # Get edited args from Agent Inbox
            edited_args = response["args"]["args"]

            # Update the AI message's tool call with edited content (reference to the message in the state)
            ai_message = state["messages"][-1] # Get the most recent message from the state
            current_id = tool_call["id"] # Store the ID of the tool call being edited
            
            # Create a new list of tool calls by filtering out the one being edited and adding the updated version
            # This avoids modifying the original list directly (immutable approach)
            updated_tool_calls = [tc for tc in ai_message.tool_calls if tc["id"] != current_id] + [
                {"type": "tool_call", "name": tool_call["name"], "args": edited_args, "id": current_id}
            ]

            # Create a new copy of the message with updated tool calls rather than modifying the original
            # This ensures state immutability and prevents side effects in other parts of the code
            result.append(ai_message.model_copy(update={"tool_calls": updated_tool_calls}))

            # Execute the tool with edited args for supported tools
            if tool_call["name"] in hitl_tools:
                 # Execute the tool with edited args
                observation = tool.invoke(edited_args)
                
                # Add only the tool response message
                result.append({"role": "tool", "content": observation, "tool_call_id": current_id})
            
            # Catch all other tool calls
            else:
                raise ValueError(f"Invalid tool call: {tool_call['name']}")

        elif response["type"] == "ignore":
            if tool_call["name"] in hitl_tools:
                # Don't execute the tool, and tell the agent how to proceed
                result.append({"role": "tool", "content": f"User ignored this {tool_call['name']} action. Ignore this and end the workflow.", "tool_call_id": tool_call["id"]})
                # Go to END
                goto = END
            else:
                raise ValueError(f"Invalid tool call: {tool_call['name']}")
            
        elif response["type"] == "response":
            # User provided feedback
            user_feedback = response["args"]
            if tool_call["name"] in hitl_tools:
                # Don't execute the tool, and add a message with the user feedback to incorporate into the draft
                result.append({"role": "tool", "content": f"User gave feedback to incorporate. Feedback: {user_feedback}", "tool_call_id": tool_call["id"]})
            else:
                raise ValueError(f"Invalid tool call: {tool_call['name']}")

        # Catch all other responses
        else:
            raise ValueError(f"Invalid response: {response}")
            
    # Update the state 
    update = {
        "messages": result,
    }

    return Command(goto=goto, update=update)

# Conditional edge function
def should_continue(state: State) -> Literal["interrupt_handler", "__end__"]:
    """Route to tool handler, or end if Done tool called"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there are no tool calls, it's just text, so we end 
    # (or potentially route back for clarification, but usually END here unless configured otherwise)
    if not last_message.tool_calls:
        return END
        
    for tool_call in last_message.tool_calls: 
        if tool_call["name"] == "Done":
            return END
    
    # If no Done tool found, go to interrupt handler
    return "interrupt_handler"


# Build workflow
agent_builder = StateGraph(State)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("interrupt_handler", interrupt_handler)

# Add edges
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "interrupt_handler": "interrupt_handler",
        END: END,
    },
)

# Compile the agent
response_agent = agent_builder.compile()

# Build overall workflow
overall_workflow = (
    StateGraph(State, input=StateInput)
    .add_node(triage_router)
    .add_node(triage_interrupt_handler)
    .add_node("response_agent", response_agent)
    .add_edge(START, "triage_router")
)

graph = overall_workflow.compile()