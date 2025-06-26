import json
import logging
import traceback
import importlib.util
from typing import Callable, Dict, Any, Optional
import time
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Check if psycopg2 is available
PSYCOPG2_AVAILABLE = importlib.util.find_spec("psycopg2") is not None

# Only import database models if psycopg2 is available
if PSYCOPG2_AVAILABLE:
    try:
        from database.models import APILogHistory, get_db_session
    except ImportError:
        PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)

# Standalone function for logging API calls
async def log_api_call(user_id: str, endpoint: str, method: str,
                      request_data: Dict[str, Any], response_data: Dict[str, Any],
                      status_code: int) -> None:
    """
    Log API call to database - can be called directly from API endpoints
    
    Args:
        user_id: ID of the user making the request (optional)
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        request_data: Request data as dictionary
        response_data: Response data as dictionary
        status_code: HTTP status code
    """
    # Skip database logging if psycopg2 is not available
    if not PSYCOPG2_AVAILABLE:
        logger.warning("Database logging skipped: psycopg2 not available")
        return
        
    try:
        # Get database session
        db = get_db_session()
        
        try:
            # Create log entry
            APILogHistory.create_log(
                session=db,
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_data=response_data,
                status_code=status_code
            )
            logger.info(f"Successfully logged API call to {endpoint}")
        except Exception as inner_e:
            logger.error(f"Error creating log entry: {str(inner_e)}")
            # Try to roll back the transaction
            try:
                db.rollback()
            except:
                pass
        finally:
            # Always close the session
            try:
                db.close()
            except:
                pass
            
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")

# Function to log API calls without waiting (for use in API endpoints)
def log_api_call_background(user_id: str, endpoint: str, method: str,
                           request_data: Dict[str, Any], response_data: Dict[str, Any],
                           status_code: int) -> None:
    """
    Log API call in the background without waiting
    """
    # Create a background task to log the API call
    asyncio.create_task(log_api_call(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        request_data=request_data,
        response_data=response_data,
        status_code=status_code
    ))

class APILoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses to the database
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing the request
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        endpoint = request.url.path
        
        # Get user ID from request (can be customized based on your auth system)
        user_id = self._get_user_id(request)
        
        # Capture request body if available
        request_body = await self._get_request_body(request)
        
        # Process the request through the application
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Create a response with the same status code and headers
        # This allows us to read the response body without consuming it
        # for the client
        
        # Capture response body
        response_body = await self._get_response_body(response)
        
        # Return the response first, then log asynchronously
        # This ensures the client gets the response without waiting for logging
        
        # Log to console immediately
        logger.info(
            f"Request: {method} {endpoint} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s | "
            f"User: {user_id or 'anonymous'}"
        )
        
        # Schedule the database logging to happen after response is sent
        # We don't await this, so it runs in the background
        import asyncio
        asyncio.create_task(self._log_to_database(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            request_data=request_body,
            response_data=response_body,
            status_code=response.status_code
        ))
        
        return response
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user ID from request (customize based on your auth system)
        """
        # Example: Get from authorization header, session, or query params
        # This is a placeholder - replace with your actual auth logic
        if "authorization" in request.headers:
            # Example: Extract from bearer token or session
            return "user-from-auth-header"  # Replace with actual extraction
        
        # Try to get from query parameters
        user_id = request.query_params.get("user_id")
        if user_id:
            return user_id
            
        # Default to None if no user ID found
        return None
    
    async def _get_request_body(self, request: Request) -> Dict[str, Any]:
        """
        Extract and parse request body
        """
        try:
            # For requests with JSON body
            if request.headers.get("content-type") == "application/json":
                body = await request.json()
                return body
            
            # For form data
            elif request.headers.get("content-type", "").startswith("multipart/form-data"):
                # For multipart form data, just log that it contained files
                form = await request.form()
                result = {}
                for key, value in form.items():
                    # Don't include actual file data in logs
                    if hasattr(value, "filename"):
                        result[key] = f"File: {value.filename}"
                    else:
                        result[key] = str(value)
                return result
            
            # For other content types, try to get body as text
            else:
                body = await request.body()
                if body:
                    return {"raw_body": str(body)}
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing request body: {str(e)}")
            return {"error": "Could not parse request body"}
    
    async def _get_response_body(self, response: Response) -> Dict[str, Any]:
        """
        Extract and parse response body
        """
        try:
            # Handle different response types
            if hasattr(response, "body"):
                # Regular response with body attribute
                body = response.body
                
                # Try to parse as JSON
                if body:
                    try:
                        if isinstance(body, bytes):
                            body_str = body.decode("utf-8")
                            return json.loads(body_str)
                        return json.loads(body)
                    except json.JSONDecodeError:
                        # If not JSON, return as string (truncated if too large)
                        if isinstance(body, bytes):
                            body_str = body.decode("utf-8", errors="replace")
                        else:
                            body_str = str(body)
                        
                        # Truncate if too large
                        if len(body_str) > 1000:
                            return {"content": body_str[:1000] + "... (truncated)"}
                        return {"content": body_str}
            else:
                # For streaming responses or responses without body
                response_type = response.__class__.__name__
                return {
                    "type": response_type,
                    "note": "Streaming response or response without body",
                    "status_code": response.status_code,
                    "media_type": getattr(response, "media_type", None)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error parsing response body: {str(e)}")
            return {"error": f"Could not parse response body: {str(e)}"}
    
    async def _log_to_database(self, user_id: str, endpoint: str, method: str, 
                             request_data: Dict[str, Any], response_data: Dict[str, Any],
                             status_code: int) -> None:
        """
        Log request and response to database
        """
        # Use the standalone function we created
        await log_api_call(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=response_data,
            status_code=status_code
        )
