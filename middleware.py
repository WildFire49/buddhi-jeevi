import os
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- API Key Security ---
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# --- API Key Validation Middleware ---
async def validate_api_key(request: Request, call_next):
    """
    Middleware for validating API key in request headers.
    
    Args:
        request (Request): The incoming request
        call_next (callable): The next middleware or route handler
        
    Returns:
        Response: Either a 403 error response or the result of the next handler
    """
    # Skip API key validation for docs
    if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
    
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    

    if not API_KEY or api_key != API_KEY:
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid or missing API key"}
        )
    
    # Continue with the request if API key is valid
    return await call_next(request)
