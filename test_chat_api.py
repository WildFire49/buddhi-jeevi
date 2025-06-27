#!/usr/bin/env python3
import json
from schemas import ChatRequest
from request_handler.chat_request_handler import process_chat

def test_chat_api():
    """Test function to check chat API response with UI components"""
    print("Testing chat API response with UI components...")
    
    # Create a test request that should trigger the video consent UI
    request = ChatRequest(
        prompt="show video consent screen",
        session_id="test_session_2003",
        type="PROMPT"
    )
    
    # Process the chat request
    response = process_chat(request)
    
    # Print the response
    print("Chat API Response:")
    print(json.dumps(response, indent=2))
    
    # Check if the response has UI components
    if "response" in response and isinstance(response["response"], dict):
        response_obj = response["response"]
        if "ui_components" in response_obj:
            print("\n✅ UI components found in response object")
            
            # Check if the UI components have buttons with action IDs
            def check_buttons(component):
                if isinstance(component, dict):
                    if component.get("component_type") == "button" and "properties" in component:
                        if "action" in component["properties"] and isinstance(component["properties"]["action"], dict):
                            action = component["properties"]["action"]
                            print(f"\nButton ID: {component.get('id')}")
                            print("Action properties:")
                            
                            # Check for action IDs and navigation properties
                            for key in ["action_id", "next_success_action_id", "next_err_action_id"]:
                                if key in action:
                                    print(f"✅ {key}: {action[key]}")
                                else:
                                    print(f"❌ {key} not found")
                    
                    # Process children recursively
                    if "children" in component and isinstance(component["children"], list):
                        for child in component["children"]:
                            check_buttons(child)
            
            # Process all UI components
            ui_components = response_obj.get("ui_components", {})
            if "ui_components" in ui_components and isinstance(ui_components["ui_components"], list):
                for component in ui_components["ui_components"]:
                    check_buttons(component)
        else:
            print("\n❌ No UI components found in response object")
    else:
        print("\n❌ Response object not found or not a dictionary")

if __name__ == "__main__":
    test_chat_api()
