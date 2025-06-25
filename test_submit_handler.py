import os
from request_handler.submit_request_handler import submit_data, api_executor
from schemas import DataSubmitRequest

def test_submit_data():
    """Test the submit_data function with a sample request"""
    print("Testing submit_data function...")
    
    # Create a sample request
    request = DataSubmitRequest(
        action_id="login",
        data=[
            {"key": "username", "value": "testuser"},
            {"key": "password", "value": "testpass"}
        ]
    )
    
    # Call submit_data
    result = submit_data(request)
    print("\nSubmit data result:")
    print(result)
    
    # Test if the result contains the expected keys
    if isinstance(result, dict):
        print("\nResult contains:")
        for key in result:
            print(f"- {key}: {type(result[key])}")
    
    return result

def test_api_executor():
    """Test the api_executor function with sample data"""
    print("\nTesting api_executor function...")
    
    # Sample API details
    api_details = {
        "method": "POST",
        "url": "/auth/login",
        "headers": {
            "Content-Type": "application/json"
        }
    }
    
    # Sample submitted data
    submitted_data = [
        {"key": "username", "value": "testuser"},
        {"key": "password", "value": "testpass"}
    ]
    
    # Call api_executor
    result = api_executor(api_details, submitted_data)
    print("\nAPI executor result:")
    print(result)
    
    return result

if __name__ == "__main__":
    # Test submit_data
    submit_result = test_submit_data()
    
    # Test api_executor
    executor_result = test_api_executor()
    
    print("\nAll tests completed!")
