from typing import List, Optional
from pydantic import BaseModel, Field

class KeyValuePair(BaseModel):
    key: str
    value: str

class DataSubmitRequest(BaseModel):
    session_id: str
    action_id: str
    data: List[KeyValuePair] = []

class DataSubmitResponse(BaseModel):
    session_id: str
    action_id: str
    status: str
    message: str
    ui_data: Optional[dict] = None
    api_data: Optional[dict] = None
    next_action_id: Optional[str] = None
