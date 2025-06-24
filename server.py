import re
import uuid
import json
from typing import Any, Dict, List, Optional
from rag_chain_builder import RAGChainBuilder

from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

chaiBuilder = RAGChainBuilder()

# --- FastAPI App Setup ---
app = FastAPI(
    title="Loan Onboarding Agent API",
    description="An API for interacting with the loan onboarding conversational agent.",
    version="1.0.0",
)

# --- In-memory state management ---
# In a production app, you'd use Redis, a DB, or another persistent store.

# --- Global Agent Instance ---
# Initialize the agent once on startup to avoid reloading the model on every request.


# --- Pydantic Models for API ---
class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The user's message to the agent.")
    session_id: Optional[str] = Field(
        None,
        description="The unique ID for the conversation session. If not provided, a new session will be started.",
    )
    type: str = Field(
        None,
        description="A field to provide context, e.g., PROMPT, FORM_DATA",
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Key-value pair object for form-data type requests.",
    )

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="The session ID for the ongoing conversation.")
    response: Any = Field(..., description="The agent's response - can be string or object.")
    ui_tags: List[str] = Field([], description="A list of UI component tags for the frontend.")

# --- API Endpoint ---
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main endpoint to chat with the loan onboarding agent.
    It manages the conversation state based on the session_id.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Validate request data based on type
    if request.type.upper() == "FORM_DATA" and request.data is None:
        raise HTTPException(status_code=400, detail="Data field is required for FORM_DATA requests.")
    elif request.type.upper() == "PROMPT" and request.prompt is None:
        raise HTTPException(status_code=400, detail="Prompt field is required for PROMPT requests.")

    # Try to get action directly from vector store first
    action = chaiBuilder.get_action_directly(request.prompt)
    
    if action:
        # Return the exact action structure
        return ChatResponse(
            session_id=session_id,
            response=action,
            ui_tags=[]
        )

    # If no direct action found, use the RAG chain
    response = chaiBuilder.get_chain().invoke(request.prompt)
    
    # Try to parse response as JSON if it looks like JSON
    try:
        parsed_response = json.loads(response)
        return ChatResponse(
            session_id=session_id,
            response=parsed_response,
            ui_tags=[]
        )
    except json.JSONDecodeError:
        # Return as string if not valid JSON
        return ChatResponse(
            session_id=session_id,
            response=response,
            ui_tags=[]
        )