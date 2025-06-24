import array
import re
import string
import uuid
import json
import os
from typing import Any, Dict, List, Optional, Union
from rag_chain_builder import RAGChainBuilder
from tools import VectorDBTools
from fastapi import UploadFile, File, Form, HTTPException, Depends

from fastapi import FastAPI, HTTPException
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
    language: Optional[str] = Field(
        None,
        description="User's preferred language if known. Will be auto-detected if not provided.",
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
    session_id: str = Field(..., description="The session ID for the ongoing conversation.")
    status: bool = Field(..., description="Whether the submission was successful.")
    message: str = Field(..., description="A message describing the result of the submission.")
    action_id: str = Field(..., description="The ID of the action that was performed.")
    errors: Optional[List[ErrorItem]] = Field([], description="List of errors that occurred during processing.")
    ui_tags: Optional[Dict[str, Any]] = Field({}, description="UI component tags for the frontend.")
    next_action_metadata: Optional[List[NextActionItem]] = Field([], description="Metadata about the next possible actions.")



class ChatResponse(BaseModel):
    session_id: str = Field(..., description="The session ID for the ongoing conversation.")
    response: Any = Field(..., description="The agent's response - can be string or object.")
    ui_tags: List[str] = Field([], description="A list of UI component tags for the frontend.")

# --- Helper Functions ---
def process_and_respond(prompt: str, session_id: str, detected_language: str = None):
    """
    Process a prompt and generate a response using the RAG chain.
    
    Args:
        prompt: The text prompt to process
        session_id: The session ID for the conversation
        detected_language: Optional pre-detected language
        
    Returns:
        ChatResponse object with the agent's response
    """
    if not prompt:
        raise HTTPException(status_code=400, detail="Empty prompt received")
        
    # Process the prompt through NLProcessor if language not already detected
    if not detected_language:
        processed_prompt, detected_language = chaiBuilder.process_input(prompt)
    else:
        processed_prompt = prompt
    
    # Log the language detection result
    print(f"Detected language: {detected_language}")
    
    # Try to get action directly from vector store first
    action = chaiBuilder.get_action_directly(processed_prompt, detected_language)
    
    if action:
        # Return the exact action structure
        return ChatResponse(
            session_id=session_id,
            response=action,
            ui_tags=[]
        )

    # If no direct action found, use the RAG chain
    response = chaiBuilder.get_chain().invoke(processed_prompt)
    
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

# --- API Endpoints ---
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main endpoint to chat with the loan onboarding agent using text prompts.
    It manages the conversation state based on the session_id.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Validate request data based on type
    if request.type.upper() == "FORM_DATA" and request.data is None:
        raise HTTPException(status_code=400, detail="Data field is required for FORM_DATA requests.")
    elif request.type.upper() == "PROMPT" and request.prompt is None:
        raise HTTPException(status_code=400, detail="Prompt field is required for PROMPT requests.")
    
    return process_and_respond(request.prompt, session_id)
    
@app.post("/chat/audio")
async def chat_audio(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Endpoint to chat with the loan onboarding agent using audio input.
    The audio will be transcribed and processed through the NLProcessor.
    """
    try:
        # Generate session ID if not provided
        session_id = session_id or str(uuid.uuid4())
        
        # Process the audio file
        transcribed_text, detected_language = chaiBuilder.nlp_processor.process_audio_input(
            audio.file, 
            filename=audio.filename
        )
        
        if not transcribed_text:
            raise HTTPException(
                status_code=400, 
                detail="Could not transcribe audio. Please try again or use text input."
            )
            
        print(f"Transcribed: '{transcribed_text}'")
        
        # Process the transcribed text and respond
        return process_and_respond(transcribed_text, session_id, detected_language)
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

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
            status=False,
            message="Data field is required for submissions.",
            action_id=action_id,
            errors=[ErrorItem(key="data", error="This field is required")],
            ui_tags={},
            next_action_metadata=[]
        )
    
    # Convert the list of KeyValuePair to a dictionary for processing if needed
    data_dict = {item.key: item.value for item in request.data}
    
    # Search for relevant data in the vector database based on action_id
    vector_results = vector_tools.search_by_action_id(action_id)
    
    # Process the results
    action_data = []
    if vector_results:
        for result in vector_results:
            action_data.append({
                "id": result.get("id"),
                "content": result.get("content"),
                "metadata": result.get("metadata")
            })
    
    # Here you can process the data as needed
    # For example, store it in a database, use it to update the RAG system, etc.
    
    # Determine next actions based on vector search results
    next_actions = []
    
    # If we found relevant actions in the vector database, suggest them
    if action_data:
        # Extract potential next actions from the metadata if available
        for item in action_data:
            metadata = item.get("metadata", {})
            next_action_id = metadata.get("next_action_id")
            next_action_text = metadata.get("next_action_text")
            
            if next_action_id and next_action_text:
                next_actions.append(
                    NextActionItem(
                        next_action_id=next_action_id,
                        suggestion_text=next_action_text
                    )
                )
    
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
    
    return DataSubmitResponse(
        session_id=session_id,
        status=True,
        message=f"Data received for action: {action_id}",
        action_id=action_id,
        errors=[],
        ui_tags={
            "show_confirmation": True, 
            "data": data_dict,
            "action_data": action_data  # Include the vector search results
        },
        next_action_metadata=next_actions
    )


# Start the server when this file is run directly
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Create temp directory for audio files if it doesn't exist
    os.makedirs("temp_audio", exist_ok=True)
    
    print("Starting server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)