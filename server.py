import uuid
import json
import os
from dotenv import load_dotenv
from rag_chain_builder import RAGChainBuilder
from tools import VectorDBTools
from middleware import validate_api_key
from utils.util import update_component_ids
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
        response_content = process_chat(request)
        
        # Debug the full response content
        print(f"Full response content from chat_request_handler: {response_content}")
        print(f"Response content type: {type(response_content)}")
        
        if isinstance(response_content, dict):
            print(f"Response content keys: {response_content.keys()}")
            for key, value in response_content.items():
                print(f"Key: {key}, Value type: {type(value)}, Value: {value if not isinstance(value, str) or len(str(value)) < 100 else value[:100] + '...'}")
        else:
            print(f"Response content is not a dict: {response_content}")
        
        # Extract UI components if they exist
        ui_components = None
        if isinstance(response_content, dict) and "ui_components" in response_content:
            ui_components = response_content.get("ui_components")
            if ui_components:
                print(f"Found UI components with ID: {ui_components.get('id', 'unknown')}")
            else:
                print("UI components is None")
                ui_components = None
        
        # Extract action IDs if they exist
        action_id = None
        next_success_action_id = None
        next_err_action_id = None
        title = None
        
        # Debug the response content
        print(f"Response content keys: {response_content.keys() if isinstance(response_content, dict) else 'Not a dict'}")
        
        if isinstance(response_content, dict):
            # Directly extract action IDs from the top level
            action_id = response_content.get("id")
            next_success_action_id = response_content.get("next_success_action_id")
            next_err_action_id = response_content.get("next_err_action_id")
            title = response_content.get("title", "")

        # Log the response type for debugging
        print(f"Response type: {type(response_content)}, Action ID: {action_id}")
        
        # Pass through all data from the NLP layer
        if isinstance(response_content, dict):
            # Extract all the fields we need
            response_text = response_content.get("response", "")
            english_response = response_content.get("english_response", None)
            nlp_response = response_content.get("nlp_response", None)
            detected_language = response_content.get("detected_language", None)
            audio_url = response_content.get("audio_url", None)
            nlp_ui_tags = response_content.get("ui_tags", [])
            
            # Re-extract action IDs from the response content as they might be at the top level
            # This ensures we get the action IDs even if they weren't extracted earlier
            action_id = response_content.get("id", action_id)
            next_success_action_id = response_content.get("next_success_action_id", next_success_action_id)
            next_err_action_id = response_content.get("next_err_action_id", next_err_action_id)
            title = response_content.get("title", title)
            
            print(f"Final extracted values - Action ID: {action_id}, Next Success: {next_success_action_id}, Next Error: {next_err_action_id}")
            print(f"English Response: {english_response}, NLP Response: {nlp_response is not None}")
            
            # Set UI tags
            combined_ui_tags = nlp_ui_tags
            if ui_components:
                combined_ui_tags.append("ui_components")
            
            # Return the formatted response with all data from NLP layer
            return ChatResponse(
                session_id=session_id,
                response=response_text,
                english_response=english_response,
                detected_language=detected_language,
                audio_url=audio_url,
                nlp_response=nlp_response,
                ui_tags=combined_ui_tags,
                ui_components=ui_components if ui_components else None,
                action_id=action_id,
                next_success_action_id=next_success_action_id,
                next_err_action_id=next_err_action_id,
                title=title 
            )
        else:
            # Handle non-dict responses
            return ChatResponse(
                session_id=session_id,
                response=response_content,
                english_response=None,
                detected_language=None,
                audio_url=None,
                nlp_response=None,
                ui_tags=["ui_components"] if ui_components else [],
                ui_components=ui_components,
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
            english_response=f"Error: {str(e)}",  # Include English version of the error
            detected_language=None,
            audio_url=None,
            nlp_response=None,
            ui_tags=[],
            ui_components=None,
            action_id=None,
            next_success_action_id=None,
            next_err_action_id=None,
            title=None
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
        next_actions = []
        
        ui_data = vector_results.get('ui_components', [])
        next_action_ui_components = vector_results.get('next_action_ui_components', [])
        
        # Prepare the response with all schema data
        return DataSubmitResponse(
            session_id=session_id,
            status="success",
            message="Data processed successfully",
            errors=[],  
            ui_data=update_component_ids(ui_data),
            next_action_ui_components=update_component_ids(next_action_ui_components)
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
            ui_data=[],  # Ensure this is an empty dict, not a list
            next_action_ui_components=[]
        )


# Start the server when this file is run directly
if __name__ == "__main__":
    import uvicorn
    PORT = os.getenv("PORT", "8002")
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
    print("Starting server on http://localhost:" + PORT)