#!/usr/bin/env python3
import os
import sys
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from schemas import DataSubmitRequest, DataSubmitResponse

# Set environment variables for MinIO
os.environ["MINIO_ENDPOINT"] = "http://3.6.132.24"
os.environ["MINIO_PORT"] = "9000"
os.environ["MINIO_ACCESS_KEY"] = "SWMSC2SQP1ICJ0I84N81"
os.environ["MINIO_SECRET_KEY"] = "bXwJ+wFwjpb9qP1S85bVsuXceO4oJtNK7+rZCS15"
os.environ["MINIO_BUCKET"] = "llm-recordings"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import what we need from server.py
from request_handler.submit_request_handler import submit_data
from database_v2 import get_ui_schema
import time
import json

# Create a minimal FastAPI app
app = FastAPI(title="Minimal Buddhi Jeevi API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to update component IDs (copied from server.py)
def update_component_ids(components):
    """Update component IDs to ensure uniqueness."""
    if not components:
        return []
        
    timestamp = int(time.time())
    
    # Handle both dictionaries and lists
    if isinstance(components, dict):
        if 'id' in components:
            # Append timestamp to the ID to ensure uniqueness
            if '$' not in components['id']:
                components['id'] = f"{components['id']}${timestamp}"
                
            # Process children recursively
            if 'children' in components and components['children']:
                update_component_ids(components['children'])
                
        return components
    elif isinstance(components, list):
        for component in components:
            if isinstance(component, dict):
                update_component_ids(component)
        return components
    return components

# Function to send API response
def send_api_response(request, response_obj, status_code=200, request_data=None):
    """Format and send API response."""
    return {
        "status_code": status_code,
        "body": response_obj.model_dump() if hasattr(response_obj, "model_dump") else response_obj
    }

# Submit endpoint
@app.post("/submit")
async def submit_handler(request: Request, submit_request: DataSubmitRequest):
    """Handle submit requests with minimal external dependencies."""
    session_id = submit_request.session_id
    action_id = submit_request.action_id
    request_data = await request.json()
    
    logger.info(f"Handling submit request for action_id: {action_id}")
    
    try:
        # Process the submitted data
        result = submit_data(submit_request)
        
        # Extract components and update their IDs with timestamps
        ui_components = result.get("ui_components", [])
        next_action_ui_components = result.get("next_action_ui_components", [])
        
        # Update component IDs with timestamps
        ui_components = update_component_ids(ui_components) if ui_components else []
        next_action_ui_components = update_component_ids(next_action_ui_components) if next_action_ui_components else []
        
        # Get other metadata from the components
        ui_id = None
        screen_id = None
        title = None
        
        # Find UI schema to extract additional metadata
        ui_schemas = get_ui_schema()
        for schema in ui_schemas:
            if schema.get('id') == f'ui_{action_id.replace("-", "_")}_001' or schema.get('id') == f'ui_{action_id}_001':
                ui_id = schema.get('id')
                screen_id = schema.get('screen_id')
                title = schema.get('title', action_id)
                break
        
        # Build the structured response
        structured_response = {
            "session_id": session_id,
            "response": {
                "ui_components": {
                    "id": ui_id,
                    "session_id": f"session_{ui_id}" if ui_id else "",
                    "screen_id": screen_id,
                    "ui_components": ui_components
                },
                "id": action_id,
                "ui_id": ui_id,
                "screen_id": screen_id,
                "type": "action",
                "title": title,
                "next_success_action_id": result.get("next_action_id"),
                "next_err_action_id": None
            },
            "ui_tags": {
                "id": f"{ui_id}$timestamp" if ui_id else "",
                "session_id": f"session_{ui_id}" if ui_id else "",
                "screen_id": screen_id,
                "ui_components": next_action_ui_components
            },
            "action_id": action_id,
            "next_success_action_id": result.get("next_action_id"),
            "next_err_action_id": None,
            "title": title
        }
        
        # Send successful response
        submit_response = DataSubmitResponse(
            session_id=session_id,
            status="success",
            message="Submit successful",
            errors=[],
            ui_data=ui_components,
            next_action_ui_components=next_action_ui_components
        )
        
        # Return both the pydantic model and structured response for comparison
        response = send_api_response(request, structured_response, 200, request_data)
        logger.info("Submit request handled successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing submit request: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Create error response
        error_response = DataSubmitResponse(
            session_id=session_id,
            status="failure",
            message=f"Error processing submission: {str(e)}",
            errors=[str(e)],
            ui_data=[],
            next_action_ui_components=[]
        )
        return send_api_response(request, error_response, 500, request_data)

if __name__ == "__main__":
    import uvicorn
    PORT = 8003  # Changed from 8002 to avoid conflict
    print(f"Starting minimal server on http://0.0.0.0:{PORT}")
    print("This server bypasses PostgreSQL and other external dependencies")
    print("Use it to test the /submit endpoint's property preservation")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
