from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

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
    ui_data: List[Any] = []  # UI schema data
    next_action_ui_components: List[Any] = []  # List of next action items

class ImageUploadResponse(BaseModel):
    status: str = Field(..., description="Status of the upload operation (success/failure)")
    message: str = Field(..., description="Message describing the result of the operation")
    image_ids: List[str] = Field([], description="List of unique IDs for the uploaded images")
    errors: List[str] = Field([], description="List of errors if any occurred during upload")


class SignedUrlRequest(BaseModel):
    object_key: str = Field(..., description="The object key/prefix to generate a signed URL for")


class SignedUrlResponse(BaseModel):
    status: str = Field(..., description="Status of the operation (success/failure)")
    message: str = Field(..., description="Message describing the result of the operation")
    url: Optional[str] = Field(None, description="The generated signed URL")
    error: Optional[str] = Field(None, description="Error message if any occurred")

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="The session ID for the ongoing conversation.")
    response: Any = Field(..., description="The agent's response - can be string or object.")
    ui_tags: Any = Field([], description="A list of UI components or tags for the frontend.")
    action_id: Optional[str] = Field(None, description="The ID of the action being performed.")
    next_success_action_id: Optional[str] = Field(None, description="The ID of the next action to be performed on success.")
    next_err_action_id: Optional[str] = Field(None, description="The ID of the next action to be performed on error.")
    title: Optional[str] = Field(None, description="The title of the action.")