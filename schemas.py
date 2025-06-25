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
    ui_data: Dict[str, Any] = {}  # UI schema data
    api_data: Dict[str, Any] = {}  # API schema data
    next_actions: List[NextActionItem] = []  # List of next action items

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="The session ID for the ongoing conversation.")
    response: Any = Field(..., description="The agent's response - can be string or object.")
    ui_tags: Any = Field([], description="A list of UI components or tags for the frontend.")
    action_id: Optional[str] = Field(None, description="The ID of the action being performed.")
    next_success_action_id: Optional[str] = Field(None, description="The ID of the next action to be performed on success.")
    next_err_action_id: Optional[str] = Field(None, description="The ID of the next action to be performed on error.")
    title: Optional[str] = Field(None, description="The title of the action.")