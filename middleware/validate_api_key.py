import os
from fastapi import Request, HTTPException
from typing import Callable, Awaitable
import logging

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
    # Get API key from environment variable
    api_key = os.getenv("API_KEY")
    
    # Skip validation if no API key is configured
    if not api_key:
        logger.warning("No API key configured, skipping validation")
        return await call_next(request)
    
    # Skip validation for certain paths
    excluded_paths = ["/docs", "/redoc", "/openapi.json", "/health"]
    if any(request.url.path.startswith(path) for path in excluded_paths):
        return await call_next(request)
    
    # Get API key from request header
    request_api_key = request.headers.get("X-API-Key")
    
    # Validate API key
    if not request_api_key or request_api_key != api_key:
        logger.warning(f"Invalid API key for {request.url.path}")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Continue processing the request
    return await call_next(request)
