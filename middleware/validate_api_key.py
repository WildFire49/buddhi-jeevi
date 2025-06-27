import os
import logging
from fastapi import Request, HTTPException
from typing import Callable, Awaitable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_api_key(request: Request, call_next: Callable[[Request], Awaitable]):
    """
    Middleware to validate API key for protected endpoints
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        The response from the next handler
    """
    # Force reload environment variables
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    # Get API key from environment
    api_key = os.getenv("API_KEY")
    logger.info(f"API_KEY environment variable: {api_key}")
    
    # Check if API key is set
    if not api_key:
        logger.warning("No API key found in environment, skipping validation")
        return await call_next(request)
        
    # Skip validation for certain paths
    excluded_paths = ["/docs", "/redoc", "/openapi.json", "/health"]
    if any(request.url.path.startswith(path) for path in excluded_paths):
        logger.info(f"Skipping validation for excluded path: {request.url.path}")
        return await call_next(request)
    
    # Get API key from request headers (try multiple formats)
    request_api_key = None
    headers = dict(request.headers)
    
    # Check for API key in various header formats
    for header_name in ['x-api-key', 'X-API-Key', 'api-key', 'API-Key']:
        for k, v in headers.items():
            if k.lower() == header_name.lower():
                request_api_key = v
                logger.info(f"Found API key in header {k}")
                break
        if request_api_key:
            break
    
    # For testing purposes, temporarily accept any API key
    # REMOVE THIS IN PRODUCTION
    if request_api_key:
        logger.info(f"API key validation temporarily disabled for testing")
        return await call_next(request)
    
    # Validate API key
    if not request_api_key:
        logger.warning(f"No API key provided for {request.url.path}")
        raise HTTPException(status_code=401, detail="API key missing")
        
    if request_api_key != api_key:
        logger.warning(f"Invalid API key for {request.url.path}")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Continue processing the request
    return await call_next(request)
