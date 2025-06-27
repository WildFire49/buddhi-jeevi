import json
import datetime
from typing import Any, Dict, List, Union

def print_response(response_data: Union[Dict, List, str, Any]) -> None:
    """
    Print the response data in a structured and readable format.
    
    Args:
        response_data: The response data to print (can be dictionary, list, string, or other type)
    """
    print("\n" + "-"*50)
    print(f"Response received at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*50)
    
    if isinstance(response_data, dict):
        # Print each key-value pair in the dictionary with proper indentation for nested structures
        print_dict(response_data)
    elif isinstance(response_data, list):
        # Handle lists
        print_list(response_data)
    else:
        # If it's not a dictionary or list, just print the whole response
        print(response_data)
    
    print("-"*50 + "\n")

def print_dict(data: Dict, indent: int = 0) -> None:
    """
    Recursively print a dictionary with proper indentation for nested structures.
    
    Args:
        data: Dictionary to print
        indent: Current indentation level
    """
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{' ' * indent}{key}:")
            print_dict(value, indent + 4)
        elif isinstance(value, list):
            print(f"{' ' * indent}{key}:")
            print_list(value, indent + 4)
        else:
            print(f"{' ' * indent}{key}: {value}")

def print_list(data: List, indent: int = 0) -> None:
    """
    Print a list with proper indentation.
    
    Args:
        data: List to print
        indent: Current indentation level
    """
    for i, item in enumerate(data):
        if isinstance(item, dict):
            print(f"{' ' * indent}Item {i+1}:")
            print_dict(item, indent + 4)
        elif isinstance(item, list):
            print(f"{' ' * indent}Item {i+1}:")
            print_list(item, indent + 4)
        else:
            print(f"{' ' * indent}- {item}")

def main():
    # Example responses to print
    simple_response = "This is a simple text response"
    
    dict_response = {
        "status": "success",
        "code": 200,
        "data": {
            "name": "John Doe",
            "email": "john@example.com",
            "details": {
                "age": 30,
                "location": "New York"
            },
            "tags": ["user", "premium", "active"]
        }
    }
    
    list_response = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2", "details": {"color": "red", "size": "medium"}},
        "Simple string item",
        [1, 2, 3, 4]
    ]
    
    # Print each response
    print("Printing simple response:")
    print_response(simple_response)
    
    print("Printing dictionary response:")
    print_response(dict_response)
    
    print("Printing list response:")
    print_response(list_response)
    
    # Simulate JSON response from API
    json_str = '{"result": {"id": "12345", "message": "Operation completed", "items": [{"name": "Item A", "value": 10}, {"name": "Item B", "value": 20}]}}'
    json_response = json.loads(json_str)
    
    print("Printing JSON response:")
    print_response(json_response)

if __name__ == "__main__":
    main()
