import uuid
import json
import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional
from storage.minio_service import MinioService
from rag_chain_builder import RAGChainBuilder
from tools import VectorDBTools
from middleware.validate_api_key import validate_api_key
from middleware.api_logger import log_api_call_background
from database.models import init_db
from utils.util import update_component_ids
from utils.api_utils import send_api_response, extract_request_body
from schemas import (
    ChatRequest, DataSubmitRequest, DataSubmitResponse,
    NextActionItem, ChatResponse, KeyValuePair, ImageUploadResponse,
    SignedUrlRequest, SignedUrlResponse
)
from request_handler.submit_request_handler import submit_data
from request_handler.chat_request_handler import process_chat
from fastapi import File, UploadFile, Form
from typing import List, Dict, Any
from pydantic import BaseModel


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

# --- API Logger Middleware ---
# app.add_middleware(APILoggerMiddleware)

# --- Initialize Database ---
try:
    # Check if psycopg2 is available
    try:
        import psycopg2
        print("psycopg2 is installed, initializing database...")
        init_db()
    except ImportError:
        print("psycopg2 is not installed. API logging to database will be disabled.")
        print("To enable database logging, install psycopg2-binary package.")
except Exception as e:
    print(f"Error initializing database: {e}")
    print("API will continue to run, but database logging may not work.")
    # Continue running the app even if DB init fails

# --- In-memory state management ---
# In a production app, you'd use Redis, a DB, or another persistent store.

# --- Global Agent Instance ---
# Initialize the agent once on startup to avoid reloading the model on every request.

# --- API Endpoint ---
@app.post("/chat")
async def chat(request_obj: Request, chat_request: ChatRequest):
    """
    Main endpoint to chat with the loan onboarding agent.
    It manages the conversation state based on the session_id.
    """
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    # Prepare request data for logging
    request_data = {
        "session_id": session_id,
        "type": chat_request.type,
        "prompt": chat_request.prompt[:100] + "..." if chat_request.prompt and len(chat_request.prompt) > 100 else chat_request.prompt,
        "has_data": chat_request.data is not None
    }

    # Validate request data based on type
    if chat_request.type and chat_request.type.upper() == "FORM_DATA" and chat_request.data is None:
        error_response = ChatResponse(
            session_id=session_id,
            response="Data field is required for FORM_DATA requests.",
            ui_tags=[],
            action_id=None,
            next_success_action_id=None,
            next_err_action_id=None
        )
        return send_api_response(request_obj, error_response, 400, request_data=request_data)
        
    elif chat_request.type and chat_request.type.upper() == "PROMPT" and chat_request.prompt is None:
        error_response = ChatResponse(
            session_id=session_id,
            response="Prompt field is required for PROMPT requests.",
            ui_tags=[],
            action_id=None,
            next_success_action_id=None,
            next_err_action_id=None
        )
        return send_api_response(request_obj, error_response, 400, request_data=request_data)
        
    elif not chat_request.prompt:
        error_response = ChatResponse(
            session_id=session_id,
            response="Prompt field is required for all chat requests.",
            ui_tags=[],
            action_id=None,
            next_success_action_id=None,
            next_err_action_id=None
        )
        return send_api_response(request_obj, error_response, 400, request_data=request_data)

    try:
        # Process the chat request using our handler
        print(f"Processing chat request with prompt: {chat_request.prompt[:50]}...")
        result = process_chat(chat_request)
        
        # Extract the response and UI components
        response_content = result.get("response", {})
        
        # For /chat API, ui_components should be a flat structure, not nested or duplicated
        if isinstance(response_content, dict) and "ui_components" in response_content:
            ui_components = response_content.get("ui_components", [])
            
            # Make sure ui_components is directly accessible and not nested
            if isinstance(ui_components, dict) and "ui_components" in ui_components:
                # Extract the inner ui_components array to avoid nesting
                ui_components = ui_components.get("ui_components", [])
                # Update the response to use the flat structure
                response_content["ui_components"] = ui_components
                print(f"Flattened ui_components structure for /chat API")
        else:
            ui_components = []
        
        # Extract action IDs if they exist
        action_id = response_content.get("id")
        next_success_action_id = response_content.get("next_success_action_id")
        next_err_action_id = response_content.get("next_err_action_id")
        title= response_content.get("title", "")

        # Log the response type for debugging
        print(f"Response type: {type(response_content)}, Action ID: {action_id}")
        
        # For ui_tags, we need to ensure we're working with the flattened ui_components
        # before updating the IDs
        flat_ui_components = ui_components
        
        # Create updated UI components for ui_tags with IDs appended with timestamp
        # Make sure we're working with a list
        if isinstance(flat_ui_components, list):
            ui_tags_array = update_component_ids(flat_ui_components)
        else:
            # If somehow we still have a dict with nested ui_components
            if isinstance(flat_ui_components, dict) and "ui_components" in flat_ui_components:
                ui_tags_array = update_component_ids(flat_ui_components["ui_components"])
            else:
                ui_tags_array = []
        
        # Create the response object
        response = ChatResponse(
            session_id=session_id,
            response=response_content,
            ui_tags=ui_tags_array,  # Use the array
            action_id=action_id,
            next_success_action_id=next_success_action_id,
            next_err_action_id=next_err_action_id,
            title=title 
        )
        
        # Send the response with logging
        return send_api_response(request_obj, response, 200, request_data=request_data)
        
    except Exception as e:
        print(f"Error processing chat request: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Create error response
        error_response = ChatResponse(
            session_id=session_id,
            response=f"An error occurred while processing your request: {str(e)}",
            ui_tags=[],
            action_id=None,
            next_success_action_id=None,
            next_err_action_id=None
        )
        
        # Send the error response with logging
        return send_api_response(request_obj, error_response, 500, request_data=request_data)

@app.post("/submit")
async def submit_endpoint(request_obj: Request, submit_request: DataSubmitRequest):
    """
    Endpoint to submit form data as an array of key-value pairs.
    """
    session_id = submit_request.session_id or str(uuid.uuid4())
    action_id = submit_request.action_id
    
    # Prepare request data for logging
    request_data = {
        "session_id": session_id,
        "action_id": action_id,
        "data_count": len(submit_request.data) if submit_request.data else 0
    }
    
   
    try:
          
        # Search for relevant data in the vector database based on action_id
        print(f"Calling submit_data with action_id: {action_id}")
        vector_results = submit_data(submit_request)
        print(f"Received vector_results: {type(vector_results)}")
        
        # Initialize empty values
        ui_data = []
        next_actions = []
        
        # Extract UI components if they exist in the response
        if isinstance(vector_results, dict) and "ui_components" in vector_results:
            raw_ui_components = vector_results.get("ui_components", [])
            
            # Ensure ui_components is always an array
            if isinstance(raw_ui_components, dict):
                # If it's a single object, wrap it in an array
                ui_data = [raw_ui_components]
                print(f"Converted single UI component object to array with 1 item")
            elif isinstance(raw_ui_components, list):
                ui_data = raw_ui_components
                print(f"Found {len(ui_data)} UI components in array")
            else:
                print("UI components is neither dict nor list, using empty array")
                ui_data = []
            
            # For submit API, we need a flat structure without nested components
            ui_data = transform_ui_schema_to_flat_structure(ui_data)
            print(f"Transformed UI components to flat structure for submit API")
        
        # Ensure next_action_ui_components is always an array
        next_action_ui_components = []
        if isinstance(vector_results, dict) and "next_action_ui_components" in vector_results:
            raw_next_action_ui_components = vector_results.get("next_action_ui_components", [])
            
            # Ensure next_action_ui_components is always an array
            if isinstance(raw_next_action_ui_components, dict):
                # If it's a single object, wrap it in an array
                next_action_ui_components = [raw_next_action_ui_components]
                print(f"Converted single next action UI component object to array with 1 item")
            elif isinstance(raw_next_action_ui_components, list):
                next_action_ui_components = raw_next_action_ui_components
                print(f"Found {len(next_action_ui_components)} next action UI components in array")
            else:
                print("Next action UI components is neither dict nor list, using empty array")
                next_action_ui_components = []
            
            # For submit API, we need a flat structure without nested components
            next_action_ui_components = transform_ui_schema_to_flat_structure(next_action_ui_components)
            print(f"Transformed next action UI components to flat structure for submit API")
        
        # For submit API, replace ui_data with next_action_ui_components
        if next_action_ui_components and len(next_action_ui_components) > 0:
            # Replace ui_data with next_action_ui_components
            ui_data = next_action_ui_components
            print(f"Replaced ui_data with {len(next_action_ui_components)} next action UI components")
        
        # Create the response object
        response = DataSubmitResponse(
            session_id=session_id,
            status="success",
            message="Data processed successfully",
            errors=[],  
            ui_data=update_component_ids(ui_data),
            next_action_ui_components=update_component_ids(next_action_ui_components)
        )
        
        # Send the response with logging
        return send_api_response(request_obj, response, 200, request_data=request_data)
        
    except Exception as e:
        print(f"Error processing submission: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Create error response
        error_response = DataSubmitResponse(
            session_id=session_id,
            status="failure",
            message=f"Error processing submission: {str(e)}",
            errors=[str(e)],
            ui_data=[],  # Ensure this is an empty list
            next_action_ui_components=[]
        )
        
        # Send the error response with logging
        return send_api_response(request_obj, error_response, 500, request_data=request_data)


# Initialize MinIO service
minio_service = MinioService()

@app.post("/upload-images")
async def upload_images(request: Request, files: List[UploadFile] = File(...)):
    """
    Upload multiple images to MinIO storage
    
    Args:
        request: The request object
        files: List of files to upload
        
    Returns:
        ImageUploadResponse: Response with image IDs
    """
    # Capture request information for logging
    method = request.method
    endpoint = request.url.path
    user_id = request.headers.get("X-API-Key", None)  # Or extract from your auth system
    
    # Capture request body for logging
    request_data = {}
    for i, file in enumerate(files):
        request_data[f"file_{i}"] = file.filename
    
    try:
        # Check if files were provided
        if not files:
            response = ImageUploadResponse(
                status="failure",
                message="No files were provided",
                image_ids=[],
                errors=["No files were provided"]
            )
            
            # Log the API call
            log_api_call_background(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response.dict(),
                status_code=422  # Unprocessable Entity
            )
            
            return response
        
        # Process each file
        image_ids = []
        errors = []
        
        for file in files:
            try:
                # Read file content
                file_content = await file.read()
                
                # Check if it's an image
                content_type = file.content_type
                
                # Upload to MinIO
                image_id = minio_service.upload_file(
                    file_data=file_content,
                    file_name=file.filename,
                    content_type=content_type
                )
                
                # Add to list of image IDs
                image_ids.append(image_id)
                
            except Exception as e:
                print(f"Error uploading {file.filename}: {str(e)}")
                errors.append(f"Error uploading {file.filename}: {str(e)}")
        
        # Prepare response
        if image_ids:
            response = ImageUploadResponse(
                status="success" if not errors else "partial_success",
                message=f"Successfully uploaded {len(image_ids)} images" + 
                        (f" with {len(errors)} errors" if errors else ""),
                image_ids=image_ids,
                errors=errors
            )
            
            # Log the API call
            log_api_call_background(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response.dict(),
                status_code=200  # Success
            )
            
            return response
        else:
            response = ImageUploadResponse(
                status="failure",
                message="Failed to upload any images",
                image_ids=[],
                errors=errors
            )
            
            # Log the API call
            log_api_call_background(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response.dict(),
                status_code=400  # Bad Request
            )
            
            return response
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        response = ImageUploadResponse(
            status="failure",
            message=f"Error processing upload: {str(e)}",
            image_ids=[],
            errors=[str(e)]
        )
        
        # Log the API call with error
        log_api_call_background(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=response.dict(),
            status_code=500  # Internal Server Error
        )
        
        return response

@app.post("/get-signed-url")
async def get_signed_url(request_obj: Request, signed_request: SignedUrlRequest):
    """
    Generate a signed URL for accessing an object in MinIO
    
    Args:
        request_obj: The FastAPI request object
        signed_request: SignedUrlRequest with object_key
        
    Returns:
        SignedUrlResponse with the signed URL or error
    """
    # Capture request information for logging
    method = request_obj.method
    endpoint = request_obj.url.path
    user_id = request_obj.headers.get("X-API-Key", None)  # Or extract from your auth system
    
    # Capture request body for logging
    request_data = {"object_key": signed_request.object_key}
    
    try:
        # Get the object key from the request
        object_key = signed_request.object_key
        
        if not object_key:
            response = SignedUrlResponse(
                status="failure",
                message="Object key is required",
                error="Missing object key"
            )
            
            # Log the API call
            log_api_call_background(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response.dict(),
                status_code=400  # Bad Request
            )
            
            return response
        
        # Get the signed URL from MinIO service
        url = minio_service.get_file_url(object_key)
        
        if url:
            response = SignedUrlResponse(
                status="success",
                message="Signed URL generated successfully",
                url=url
            )
            
            # Log the API call
            log_api_call_background(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response.dict(),
                status_code=200  # Success
            )
            
            return response
        else:
            response = SignedUrlResponse(
                status="failure",
                message="Failed to generate signed URL",
                error="Object not found or error generating URL"
            )
            
            # Log the API call
            log_api_call_background(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response.dict(),
                status_code=404  # Not Found
            )
            
            return response
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        response = SignedUrlResponse(
            status="failure",
            message=f"Error generating signed URL: {str(e)}",
            error=str(e)
        )
        
        # Log the API call with error
        log_api_call_background(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=response.dict(),
            status_code=500  # Internal Server Error
        )
        
        return response

def transform_ui_schema_to_frontend_structure(ui_components):
    """
    Transform ChromaDB UI schema structure to expected frontend structure.
    Converts nested 'ui_components' to 'components' and ensures consistent structure.
    """
    if not ui_components:
        return []
    
    transformed_components = []
    
    for component in ui_components:
        if isinstance(component, dict):
            # Create the expected frontend structure
            transformed_component = {
                "id": component.get("id", "unknown"),
                "type": "screen",  # Default type for UI components
            }
            
            # Check if this is a ChromaDB UI schema structure (has nested ui_components)
            if "ui_components" in component:
                # Transform nested ui_components to components
                nested_components = component["ui_components"]
                transformed_component["components"] = transform_nested_components(nested_components)
            elif "components" in component:
                # Already in correct structure
                transformed_component["components"] = component["components"]
            else:
                # Single component, wrap in components array
                transformed_component["components"] = [component]
            
            transformed_components.append(transformed_component)
        else:
            # Handle non-dict components
            transformed_components.append(component)
    
    return transformed_components

def transform_nested_components(nested_components):
    """
    Transform nested UI components from ChromaDB format to frontend format.
    """
    if not nested_components:
        return []
    
    transformed = []
    
    for component in nested_components:
        if isinstance(component, dict):
            # Transform ChromaDB component structure to frontend structure
            frontend_component = {
                "id": component.get("id", "unknown"),
                "type": component.get("component_type", "unknown"),
            }
            
            # Add properties as direct fields for frontend
            properties = component.get("properties", {})
            if properties:
                # Map common properties to frontend structure
                if "text" in properties:
                    frontend_component["label"] = properties["text"]
                if "hint" in properties:
                    frontend_component["placeholder"] = properties["hint"]
                if "validation" in properties:
                    frontend_component["validation"] = properties["validation"]
                if "action" in properties:
                    frontend_component["action"] = properties["action"]
            
            # Handle children recursively
            if "children" in component:
                frontend_component["children"] = transform_nested_components(component["children"])
            
            transformed.append(frontend_component)
        else:
            transformed.append(component)
    
    return transformed

# app.add_middleware(APILoggerMiddleware)
def transform_ui_schema_to_flat_structure(ui_components):
    """
    Transform UI components to a flat structure for the submit API.
    Returns components directly without nesting them under a 'components' array.
    """
    if not ui_components:
        return []
    
    # If we have a list of components, process each one
    if isinstance(ui_components, list):
        # Check if these are already flat components
        if all(isinstance(comp, dict) and "component_type" in comp for comp in ui_components):
            return ui_components
        
        # Otherwise, we need to extract and flatten
        flat_components = []
        for component in ui_components:
            # If this is a container with nested ui_components, extract them
            if isinstance(component, dict):
                if "ui_components" in component:
                    # Extract the nested components
                    nested = component.get("ui_components", [])
                    flat_components.extend(transform_ui_schema_to_flat_structure(nested))
                elif "components" in component:
                    # Extract from components array
                    nested = component.get("components", [])
                    flat_components.extend(transform_ui_schema_to_flat_structure(nested))
                else:
                    # It's a single component, add it directly
                    flat_components.append(component)
        
        return flat_components
    
    # If we have a single component object with nested components
    elif isinstance(ui_components, dict):
        if "ui_components" in ui_components:
            return transform_ui_schema_to_flat_structure(ui_components["ui_components"])
        elif "components" in ui_components:
            return transform_ui_schema_to_flat_structure(ui_components["components"])
        else:
            # It's a single component
            return [ui_components]
    
    # Fallback
    return []

# Start the server when this file is run directly

if __name__ == "__main__":
    import uvicorn
    PORT = os.getenv("PORT", "8002")
    uvicorn.run(app, host="0.0.0.0", port=int(PORT))
    print("Starting server on http://localhost:" + PORT)