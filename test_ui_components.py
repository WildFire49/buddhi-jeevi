#!/usr/bin/env python3
import json
import copy
from request_handler.chat_request_handler import clean_component_ids, get_ui_components_by_id
from database_v2 import get_ui_schema, get_action_schema

def test_ui_components():
    """Test function to check UI component processing with action IDs"""
    print("Testing UI component processing...")
    
    # Get the video consent UI schema
    ui_id = "ui_video_consent_001"
    action_id = "video-consent"
    
    # Get UI components
    ui_components = get_ui_components_by_id(ui_id, action_id)
    
    if ui_components:
        print(f"Found UI components for ID: {ui_id}")
        
        # Check if the UI components have the accept button
        found_button = False
        
        def find_button(component):
            nonlocal found_button
            if isinstance(component, dict):
                if component.get("component_type") == "button" and component.get("id") == "accept_button":
                    found_button = True
                    print("Found accept button:")
                    print(json.dumps(component, indent=2))
                    
                    # Check if the button has action properties
                    if "properties" in component and "action" in component["properties"]:
                        action = component["properties"]["action"]
                        print("Button action:")
                        print(json.dumps(action, indent=2))
                        
                        # Check for action IDs and navigation properties
                        if "action_id" in action:
                            print(f"✅ action_id found: {action['action_id']}")
                        else:
                            print("❌ action_id not found")
                            
                        if "next_success_action_id" in action:
                            print(f"✅ next_success_action_id found: {action['next_success_action_id']}")
                        else:
                            print("❌ next_success_action_id not found")
                            
                        if "next_err_action_id" in action:
                            print(f"✅ next_err_action_id found: {action['next_err_action_id']}")
                        else:
                            print("❌ next_err_action_id not found")
                
                # Process children recursively
                if "children" in component and isinstance(component["children"], list):
                    for child in component["children"]:
                        find_button(child)
        
        # Process all UI components
        if "ui_components" in ui_components and isinstance(ui_components["ui_components"], list):
            for component in ui_components["ui_components"]:
                find_button(component)
        
        if not found_button:
            print("❌ Accept button not found in UI components")
    else:
        print(f"❌ No UI components found for ID: {ui_id}")

if __name__ == "__main__":
    test_ui_components()
