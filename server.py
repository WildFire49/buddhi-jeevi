import uuid
import json
import os
from dotenv import load_dotenv
from rag_chain_builder import RAGChainBuilder
from tools import VectorDBTools
from middleware import validate_api_key

from schemas import (
    ChatRequest, DataSubmitRequest, DataSubmitResponse,
    NextActionItem, ChatResponse, KeyValuePair
)
from request_handler.submit_request_handler import submit_data
from request_handler.chat_request_handler import process_chat

# Load environment variables
load_dotenv()
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

# Determine which LLM to use based on environment variables or default to Ollama
LLM_TYPE = os.getenv("LLM_TYPE", "ollama").lower()  # "ollama" or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3" if LLM_TYPE == "ollama" else "gpt-3.5-turbo")

# Initialize the RAG chain builder with the specified LLM
print(f"Initializing RAGChainBuilder with {LLM_TYPE} model: {LLM_MODEL}")
chaiBuilder = RAGChainBuilder(llm_type=LLM_TYPE, model_name=LLM_MODEL)

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

# --- API Endpoint ---
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main endpoint to chat with the loan onboarding agent.
    It manages the conversation state based on the session_id.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Validate request data based on type
    if request.type and request.type.upper() == "FORM_DATA" and request.data is None:
        raise HTTPException(status_code=400, detail="Data field is required for FORM_DATA requests.")
    elif request.type and request.type.upper() == "PROMPT" and request.prompt is None:
        raise HTTPException(status_code=400, detail="Prompt field is required for PROMPT requests.")
    elif not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt field is required for all chat requests.")

    try:
        # Process the chat request using our handler
        print(f"Processing chat request with prompt: {request.prompt[:50]}...")
        result = process_chat(request)
        
        # Extract the response and UI components
        response_content = result.get("response", {})
        
        # Extract UI components if they exist in the response
        ui_components = []
        if isinstance(response_content, dict) and "ui_components" in response_content:
            ui_components = response_content.get("ui_components", [])
            print(f"Found {len(ui_components)} UI components")
        
        # Extract action IDs if they exist
        action_id = None
        next_success_action_id = None
        next_err_action_id = None
        title= None
        if isinstance(response_content, dict):
            action_id = response_content.get("id")
            next_success_action_id = response_content.get("next_success_action_id")
            next_err_action_id = response_content.get("next_err_action_id")
            title = response_content.get("title", "")

        # Log the response type for debugging
        print(f"Response type: {type(response_content)}, Action ID: {action_id}")
        
        # Return the formatted response
        return ChatResponse(
            session_id=session_id,
            response=response_content,
            ui_tags=ui_components,
            action_id=action_id,
            next_success_action_id=next_success_action_id,
            next_err_action_id=next_err_action_id,
            title=title 
        )
    except Exception as e:
        print(f"Error processing chat request: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return an error response
        return ChatResponse(
            session_id=session_id,
            response=f"An error occurred while processing your request: {str(e)}",
            ui_tags=[],
            action_id=None,
            next_success_action_id=None,
            next_err_action_id=None
        )

@app.post("/submit")
async def submit_endpoint(request: DataSubmitRequest):
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
    
    try:
        # Convert the list of KeyValuePair to a dictionary for processing if needed
        data_dict = {item.key: item.value for item in request.data}
        
        # Search for relevant data in the vector database based on action_id
        # This now returns a dictionary with ui_components, api_details, and next_action_id
        print(f"Calling submit_data with action_id: {action_id}")
        vector_results = submit_data(request)
        print(f"Received vector_results: {type(vector_results)}")
        
        # Initialize empty values
        ui_data = {}
        api_data = {}
        next_actions = []
        
        # Process the results if they exist
        if vector_results and isinstance(vector_results, dict):
            # Extract UI components
            ui_data = vector_results.get('ui_components', {})
            print(f"UI data: {ui_data}")
            
            # Extract API details
            api_data = vector_results.get('api_details', {})
            print(f"API data: {api_data}")
            
            # Extract next action ID and create NextActionItem
            next_action_id = vector_results.get('next_action_id')
            if next_action_id:
                next_actions = [NextActionItem(
                    next_action_id=str(next_action_id),
                    suggestion_text=f"Continue to step {next_action_id}"
                )]
        else:
            print("No vector results or invalid format")
            
        # If no next actions were found, provide default options
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
            message="Data processed successfully",
            errors=[],
            ui_data=ui_data,
            api_data=api_data,
            next_actions=next_actions
        )
    except Exception as e:
        print(f"Error processing submission: {str(e)}")
        import traceback
        traceback.print_exc()
        return DataSubmitResponse(
            session_id=session_id,
            status="failure",
            message=f"Error processing submission: {str(e)}",
            errors=[str(e)],
            ui_data={},
            api_data={},
            next_actions=[]
        )


# Start the server when this file is run directly
if __name__ == "__main__":
    import uvicorn
    PORT = os.getenv("PORT", "8002")
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
    print("Starting server on http://localhost:" + PORT)