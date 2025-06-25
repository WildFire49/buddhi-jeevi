import array
import re
import string
import uuid
import json
from typing import Any, Dict, List, Optional
from rag_chain_builder import RAGChainBuilder
from tools import VectorDBTools
from middleware import validate_api_key

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

chaiBuilder = RAGChainBuilder()

# Initialize the vector DB tools
vector_tools = VectorDBTools()

# --- FastAPI App Setup ---
app = FastAPI(
    title="Loan Onboarding Agent API",
    description="An API for interacting with the loan onboarding conversational agent.",
    version="1.0.0",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Key Validation Middleware ---
app.middleware("http")(validate_api_key)

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

# --- Pydantic Models for API ---
class KeyValuePair(BaseModel):
    key: str
    value: Any

class DataSubmitRequest(BaseModel):
    session_id: Optional[str] = Field(
        None,
        description="The unique ID for the conversation session. If not provided, a new session will be started.",
    )
    action_id: str = Field(
        ...,
        description="The ID of the action being performed.",
    )
    data: Optional[List[KeyValuePair]] = Field(
        None,
        description="Array of key-value pairs for form-data type requests.",
    )

class ErrorItem(BaseModel):
    key: str
    error: str

class NextActionItem(BaseModel):
    next_action_id: str
    suggestion_text: str

class DataSubmitResponse(BaseModel):
    session_id: str
    status: str
    message: str
    errors: List[str] = []
    ui_data: Dict[str, Any] = {}  # UI schema data
    api_data: Dict[str, Any] = {}  # API schema data
    action_data: Dict[str, Any] = {}  # Action schema data
    next_action: Dict[str, Any] = {}  # Next action metadata
    next_actions: List[NextActionItem] = []  # List of next action items

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

@app.post("/submit")
async def submit_data(request: DataSubmitRequest):
    """
    Endpoint to submit form data as an array of key-value pairs.
    """
    session_id = request.session_id or str(uuid.uuid4())
    action_id = request.action_id
    
    # Process the submitted data
    if not request.data:
        return DataSubmitResponse(
            session_id=session_id,
            status="failure",
            message="Data field is required for submissions.",
            errors=["Data field is required"],
            ui_data={},
            api_data={},
            action_data={},
            next_action={},
            next_actions=[]
        )
    
    # Convert the list of KeyValuePair to a dictionary for processing if needed
    data_dict = {item.key: item.value for item in request.data}
    
    # Search for relevant data in the vector database based on action_id
    vector_results = vector_tools.search_by_action_id(action_id)
    
    # Process the results by schema type
    action_data = []
    ui_data = []
    api_data = []
    
    if vector_results:
        for result in vector_results:
            schema_type = result.get("schema_type", "unknown")
            item_data = {
                "id": result.get("id"),
                "content": result.get("content"),
                "metadata": result.get("metadata")
            }
            
            # Sort results by schema type
            if schema_type == "action":
                action_data.append(item_data)
            elif schema_type == "ui":
                ui_data.append(item_data)
            elif schema_type == "api":
                api_data.append(item_data)
            else:
                # If schema type is unknown, add to action_data as fallback
                action_data.append(item_data)
    
    # Here you can process the data as needed
    # For example, store it in a database, use it to update the RAG system, etc.
    
    # Create next_actions list from the next_action data
    next_actions = []
    next_action = {}
    
    # Process action data
    if action_data:
        # Get the first result's metadata (assuming it's the most relevant)
        metadata = action_data[0].get("metadata", {})
        
        # Extract next action if available
        if "next_action_id" in metadata:
            next_action = {
                "id": metadata.get("next_action_id"),
                "text": metadata.get("next_action_text", "")
            }
            next_actions = [
                NextActionItem(
                    next_action_id=next_action["id"],
                    suggestion_text=next_action["text"]
                )
            ]
    
    # Process UI data
    if ui_data:
        ui_metadata = ui_data[0].get("metadata", {})
        try:
            # Extract UI components if available
            if "ui_components" in ui_metadata:
                ui_components = json.loads(ui_metadata.get("ui_components", "[]"))
                ui_data_processed = {
                    "ui_id": ui_metadata.get("ui_id", ""),
                    "ui_type": ui_metadata.get("ui_type", ""),
                    "components": ui_components
                }
            # If full UI data is available, use it
            if "full_ui" in ui_metadata:
                ui_data_processed = json.loads(ui_metadata["full_ui"])
        except json.JSONDecodeError:
            ui_data_processed = {"error": "Invalid UI data format"}
    
    # Process API data
    if api_data:
        api_metadata = api_data[0].get("metadata", {})
        try:
            # Extract API details if available
            api_data_processed = {
                "api_id": api_metadata.get("api_detail_id", ""),
                "endpoint": api_metadata.get("endpoint", ""),
                "method": api_metadata.get("method", "")
            }
            # If params are available, add them
            if "params" in api_metadata:
                api_data_processed["params"] = json.loads(api_metadata.get("params", "{}"))
            # If full API data is available, use it
            if "full_api" in api_metadata:
                api_data_processed = json.loads(api_metadata["full_api"])
        except json.JSONDecodeError:
            api_data_processed = {"error": "Invalid API data format"}
    
    # If no next actions were found in the vector database, provide default options
    if not next_actions:
        next_actions = [
            NextActionItem(
                next_action_id="review_submission",
                suggestion_text="Review your submission"
            ),
            NextActionItem(
                next_action_id="submit_another",
                suggestion_text="Submit another form"
            )
        ]
    
    # Prepare the response with all schema data
    return DataSubmitResponse(
        session_id=session_id,
        status="success",
        message="Data submitted successfully",
        errors=[],
        ui_data=ui_data_processed,  # Include UI schema data
        api_data=api_data_processed,  # Include API schema data
        action_data=action_data[0].get("metadata", {}) if action_data else {},  # Include action schema data
        next_action=next_action,  # Include next action data
        next_actions=next_actions  # Include next actions list
    )


# Start the server when this file is run directly
if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)