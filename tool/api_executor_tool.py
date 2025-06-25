from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import httpx
import asyncio
from fastapi import HTTPException
import json


@dataclass
class ApiDetail:
    """Data class for individual API detail structure"""
    http_method: str
    endpoint_path: str
    request_payload_template: Dict[str, Any]


@dataclass
class ApiData:
    """Data class for the complete API data structure from /submit endpoint"""
    id: str
    api_details: List[ApiDetail]


class ApiExecutor:
    """Class to handle dynamic API execution"""
    
    def __init__(self, base_url: str = "https://a3ce5fbf-f3cc-407c-8995-ce22736cd41b.mock.pstmn.io"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def execute_api(self, processed_payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute API calls dynamically based on the API data structure
        
        Args:
            api_data: ApiData object containing API details
            processed_payload: Optional processed payload to override template
            
        Returns:
            Dictionary containing execution results
        """
        results = []
        
        try:
            for api_detail in api_data.api_details:
                # Use processed payload if provided, otherwise use template
                payload = processed_payload if processed_payload else api_detail.request_payload_template
                
                # Construct full URL
                full_url = f"{self.base_url}{api_detail.endpoint_path}"
                
                # Execute the API call
                result = await self._make_request(
                    method=api_detail.http_method,
                    url=full_url,
                    payload=payload
                )
                
                results.append({
                    "api_id": api_data.id,
                    "endpoint": api_detail.endpoint_path,
                    "method": api_detail.http_method,
                    "status": "success" if result.get("success") else "failed",
                    "response": result
                })
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "api_id": api_data.id
            }
        
        return {
            "status": "completed",
            "api_id": api_data.id,
            "results": results
        }
    
    async def _make_request(self, method: str, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request using httpx client
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Full URL to make request to
            payload: Request payload
            
        Returns:
            Dictionary containing response data
        """
        try:
            method = method.upper()
            
            if method == "GET":
                response = await self.client.get(url, params=payload)
            elif method == "POST":
                response = await self.client.post(url, json=payload)
            elif method == "PUT":
                response = await self.client.put(url, json=payload)
            elif method == "DELETE":
                response = await self.client.delete(url, json=payload)
            elif method == "PATCH":
                response = await self.client.patch(url, json=payload)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            # Check if request was successful
            response.raise_for_status()
            
            # Debug response content
            content_type = response.headers.get('content-type', '')
            
            # Try to parse JSON response
            try:
                if response.content and 'json' in content_type.lower():
                    data = response.json()
                else:
                    # Handle non-JSON responses
                    data = {"raw_content": response.text}
                    
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": data,
                    "headers": dict(response.headers),
                    "content_type": content_type
                }
            except json.JSONDecodeError as json_err:
                # Handle malformed JSON but still return a success since the HTTP call succeeded
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": {"raw_content": response.text},
                    "headers": dict(response.headers),
                    "content_type": content_type,
                    "parse_error": f"JSON parse error: {str(json_err)}"
                }
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "status_code": e.response.status_code,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "headers": dict(e.response.headers)
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except json.JSONDecodeError as json_err:
            return {
                "success": False,
                "error": f"Invalid JSON response: {str(json_err)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


def create_api_data_from_dict(data: Dict[str, Any]) -> ApiData:
    """
    Create ApiData object from dictionary
    
    Args:
        data: Dictionary containing API data structure
        
    Returns:
        ApiData object
    """
    api_details = []
    
    for detail in data.get("api_details", []):
        api_detail = ApiDetail(
            http_method=detail.get("http_method"),
            endpoint_path=detail.get("endpoint_path"),
            request_payload_template=detail.get("request_payload_template", {})
        )
        api_details.append(api_detail)
    
    return ApiData(
        id=data.get("id"),
        api_details=api_details
    )


async def execute_api_from_processed_data(processed_api_details: Dict[str, Any], processed_payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Execute API from processed data - main function to be called from submit_request_handler
    
    Args:
        processed_api_details: Processed API details dictionary
        processed_payload: Optional processed payload
        
    Returns:
        Dictionary containing execution results
    """
    try:
        # Create ApiData object from processed details
        api_data = create_api_data_from_dict(processed_api_details)
        
        # Create executor and execute API
        executor = ApiExecutor()
        result = await executor.execute_api(api_data, processed_payload)
        
        # Close the client
        await executor.close()
        
        return result
        
    except Exception as e:
        return {
            "status": "failed",
            "error": f"API execution failed: {str(e)}"
        }


# Synchronous wrapper for use in non-async contexts
def execute_api_sync(processed_api_details: Dict[str, Any], processed_payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for API execution
    
    Args:
        processed_api_details: Processed API details dictionary
        processed_payload: Optional processed payload
        
    Returns:
        Dictionary containing execution results
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If there's no event loop in this thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Use the event loop to run the coroutine
    if loop.is_running():
        # If we're in an async context (loop is already running), create a task
        # This is a workaround and might not be ideal in all cases
        return {
            "status": "api_failed",
            "message": "Cannot execute API in this context - event loop is already running"
        }
    else:
        # If we're not in an async context, run the coroutine
        return loop.run_until_complete(execute_api_from_processed_data(processed_api_details, processed_payload))