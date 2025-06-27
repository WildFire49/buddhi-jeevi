import logging
from typing import Dict, Any, Optional, TypeVar, Type
from fastapi import Request
from pydantic import BaseModel
import asyncio

from middleware.api_logger import log_api_call_background

logger = logging.getLogger(__name__)

# Generic type for response models
ResponseT = TypeVar('ResponseT', bound=BaseModel)

def send_api_response(
    request: Request,
    response_model: ResponseT,
    status_code: int = 200,
    user_id: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None
) -> ResponseT:
    """
    Common function to send API responses and log them to the database
    
    Args:
        request: The FastAPI request object
        response_model: The Pydantic response model instance
        status_code: HTTP status code
        user_id: User ID (optional, will try to extract from request if not provided)
        request_data: Request data as dictionary (optional)
        
    Returns:
        The response model instance
    """
    # Extract request information
    method = request.method
    endpoint = request.url.path
    
    # Extract user ID from request if not provided
    if user_id is None:
        user_id = request.headers.get("X-API-Key") or "anonymous"
    
    # Use empty dict if request_data not provided
    if request_data is None:
        request_data = {}
    
    # Convert response model to dict for logging
    try:
        response_data = response_model.dict()
    except AttributeError:
        # Handle case where response_model is not a Pydantic model
        response_data = {"data": str(response_model)}
    
    # Log the API call in the background
    log_api_call_background(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        request_data=request_data,
        response_data=response_data,
        status_code=status_code
    )
    
    # Return the response model
    return response_model

async def extract_request_body(request: Request) -> Dict[str, Any]:
    """
    Extract request body as a dictionary
    
    Args:
        request: The FastAPI request object
        
    Returns:
        Request body as dictionary
    """
    try:
        # For JSON requests
        if request.headers.get("content-type") == "application/json":
            return await request.json()
        
        # For form data
        elif request.headers.get("content-type", "").startswith("multipart/form-data"):
            form = await request.form()
            result = {}
            for key, value in form.items():
                # Don't include actual file data in logs
                if hasattr(value, "filename"):
                    result[key] = f"File: {value.filename}"
                else:
                    result[key] = str(value)
            return result
        
        # For other content types
        else:
            body = await request.body()
            if body:
                return {"raw_body": str(body)}
            return {}
            
    except Exception as e:
        logger.error(f"Error extracting request body: {str(e)}")
        return {"error": "Could not extract request body"}
