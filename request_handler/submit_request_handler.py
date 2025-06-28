import sys
import os
import json
import uuid
import time
import datetime
from dotenv import load_dotenv

def add_delay(seconds=2):
    """Add a deliberate delay to the execution
    
    Args:
        seconds (int): Number of seconds to delay execution
    """
    print(f"Adding delay of {seconds} seconds...")
    time.sleep(seconds)
    print("Continuing execution")

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import DataSubmitRequest, DataSubmitResponse, KeyValuePair
from rag_chain_builder import RAGChainBuilder
from langchain_core.prompts import ChatPromptTemplate
from database_v3  import get_action_schema, get_ui_schema
# Load environment variables
load_dotenv()

# Determine which LLM to use based on environment variables or default to Ollama
LLM_TYPE = os.getenv("LLM_TYPE", "ollama").lower()  # "ollama" or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3" if LLM_TYPE == "ollama" else "gpt-3.5-turbo")

def check_prompt_by_id(action_id, isNextAction: bool = False):
    action_schema = get_action_schema()
    ui_schema = get_ui_schema()
    if not action_schema or not ui_schema:
        return None
    if action_schema.get(action_id) is None:
        return None
    action = action_schema.get(action_id)
    if not action:
        return None
    if isNextAction:
        action_id_final = action.get('next_success_action_id')
    else:
        action_id_final = action.get('id')
    final_action = action_schema.get(action_id_final)
    if not final_action:
        return None
    ui_id = final_action.get('ui_id')
    ui_action = ui_schema.get(ui_id)
    if not ui_action:
        return None

    processed_results = {
        "ui_components": ui_action.get('ui_components', []),
        "next_action_ui_components": ui_action.get('ui_components', []),
        "api_details": [],
        "next_action_id": action_id_final
        }
    add_delay(25)
    return processed_results     

def submit_data(request: DataSubmitRequest):
    action_id = request.action_id
    processed_results = check_prompt_by_id(action_id, True)
    if processed_results:
        return processed_results
    
    system_prompt = """
        You are a UI component and workflow extractor. Your task is to extract specific information from the provided context.
        
        CRITICAL INSTRUCTIONS:
        1. Extract the current action's UI components from the context
        2. Find the next_success_action_id for the current action
        3. Extract ONLY the UI components that belong to the next_success_action_id - DO NOT include multiple UI schemas
        4. NEVER hallucinate or substitute values - copy all properties and URLs exactly as they appear
        5. NEVER use placeholder values like "example.com" - use the exact URLs from the source data
        6. Temperature is set to 0 - be deterministic and precise
        
        TITLE AND TEXT PRESERVATION RULES:
        - If a UI component has a "title" field, copy it EXACTLY as it appears in the source
        - If a text component has a "text" property, copy it EXACTLY without modification
        - DO NOT generate descriptive titles like "UI Components related to..." - use original values only
        - DO NOT rephrase, summarize, or modify any text content from the source data
        - The title field is displayed to end users in the frontend - it must be the original value
        
        STEP-BY-STEP EXTRACTION PROCESS:
        1. Identify the current action and its UI components
        2. Find the next_success_action_id from the current action's metadata
        3. Search for UI components that match the next_success_action_id's ui_id pattern (e.g., if next_success_action_id is "select-flow", look for "ui_select_flow_001")
        4. Return ONLY those specific UI components for the next action - not all possible UI schemas
        5. Ensure next_action_ui_components contains different components than ui_components
        6. Copy all text values, titles, and properties EXACTLY as they appear in the source
        
        VALIDATION RULES:
        - ui_components and next_action_ui_components MUST be different
        - next_action_ui_components should contain ONLY the UI schema for the next_success_action_id
        - ALL text content must be copied exactly from source data without modification
        
        Context: {context}
        
        Return a JSON object with:
        - ui_components: array of current action UI components
        - api_details: array of API details for current action
        - next_action_id: the next_success_action_id from current action
        - next_action_ui_components: array containing ONLY the UI components for the next_success_action_id (not multiple schemas)
        """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Process the context for the action related to this query: {query}")
    ])

    try:
        # Initialize RAG builder with the configured LLM type and model
        rag_builder = RAGChainBuilder(llm_type=LLM_TYPE, model_name=LLM_MODEL)
        print(f"Using {LLM_TYPE} model {LLM_MODEL} for processing action_id: {action_id}")
        # Get the response from the LLM as a dictionary
        llm_response = rag_builder.run_prompt_with_context(
            action_id, prompt, {}
        )
        if not llm_response or not isinstance(llm_response, dict):
            print(f"No valid response from LLM: {llm_response}")
            return {}
        
        # Extract components from the LLM response dictionary
        ui_components = llm_response.get('ui_components', [])
        api_details = llm_response.get('api_details', [])
        next_action_id = llm_response.get('next_action_id')
        next_action_ui_components = llm_response.get('next_action_ui_components', [])
        
        # CRITICAL VALIDATION: Ensure next_action_ui_components are different
        print(f"DEBUG: Current action_id: {action_id}")
        print(f"DEBUG: Next action_id: {next_action_id}")
        print(f"DEBUG: UI components count: {len(ui_components)}")
        print(f"DEBUG: Next UI components count: {len(next_action_ui_components)}")
        
        # Check if components are identical (this should not happen)
        if ui_components == next_action_ui_components:
            print("ERROR: next_action_ui_components are identical to ui_components!")
            print("Attempting to retrieve correct next action UI components...")
            
            # Force retrieval of correct next action UI components
            if next_action_id:
                print(f"Using targeted retrieval for next_action_id: {next_action_id}")
                
                try:
                    # Use the new targeted method to get UI components
                    targeted_components = rag_builder.get_ui_components_by_action_id(next_action_id)
                    
                    if targeted_components and len(targeted_components) > 0:
                        next_action_ui_components = targeted_components
                        print(f"Successfully retrieved {len(next_action_ui_components)} targeted components for {next_action_id}")
                        
                        # Verify they are different
                        if ui_components != next_action_ui_components:
                            print("SUCCESS: Retrieved different UI components for next action")
                        else:
                            print("WARNING: Targeted retrieval still returned identical components")
                            next_action_ui_components = []
                    else:
                        print(f"Targeted retrieval failed for {next_action_id}, setting to empty array")
                        next_action_ui_components = []
                        
                except Exception as e:
                    print(f"Error in targeted retrieval for {next_action_id}: {e}")
                    next_action_ui_components = []
        
        # Final validation
        if ui_components == next_action_ui_components and len(next_action_ui_components) > 0:
            print("WARNING: Still have identical components, clearing next_action_ui_components")
            next_action_ui_components = []
        
        data = request.data
        response = api_executor(api_details, data)
        print("api_executor", response)
       
        processed_results = {
            "ui_components": ui_components,
            "next_action_ui_components": next_action_ui_components,
            "api_details": api_details,
            "next_action_id": next_action_id
        }
        
        print(f"Found {len(processed_results)} results for action_id {action_id}")
        return processed_results
    except Exception as e:
        print(f"Error in submit_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def api_executor(api_details: dict, submited_data: list):
    try:
        # Convert submitted data from [{key: string, value: any}] to {key: value}
        converted_data = {}
        if submited_data and isinstance(submited_data, list):
            for item in submited_data:
                if isinstance(item, KeyValuePair):
                    # Access attributes of KeyValuePair using attribute notation
                    converted_data[item.key.split("$")[0]] = item.value
                elif isinstance(item, dict) and 'key' in item and 'value' in item:
                    # Fallback for dictionary format
                    converted_data[item.key.split("$")[0]] = item['value']
    
        print(f"Converted submitted data: {converted_data}")
        
        # Process the entire api_details to replace all placeholders
        processed_api_details = process_template(api_details, converted_data)
        print(f"Processed API details: {processed_api_details}")
        
        # Extract the processed payload if it exists
        processed_payload = None
        if processed_api_details and isinstance(processed_api_details, dict):
            if 'request_payload_template' in processed_api_details:
                processed_payload = processed_api_details.get('request_payload_template')
            elif isinstance(processed_api_details.get('request_payload'), dict):
                processed_payload = processed_api_details.get('request_payload')
        
        # Here you would execute the API call using processed_api_details and processed_payload
        # For now, we'll just return the processed data and details
        return {
            "data": converted_data,
            "processed_payload": processed_payload,
            "api_details": processed_api_details,
            "status": "prepared"
        }
    except Exception as e:
        print(f"Error in api_executor: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "status": "failed"
        }


def process_template(template, data):
    """
    Process a template by replacing {{key}} placeholders with values from data.
    Works recursively through nested dictionaries and lists.
    
    :param template: Template object (dict, list, or primitive value) containing placeholders
    :param data: Dictionary with key-value pairs to replace placeholders
    :return: Processed template with placeholders replaced
    """
    try:
        if template is None:
            return None
            
        # Handle list templates first
        if isinstance(template, list):
            return [process_template(item, data) for item in template]
            
        # Handle dictionary templates
        elif isinstance(template, dict):
            # Special handling for common payload fields
            if isinstance(template.get('request_payload_template'), dict):
                template['request_payload_template'] = process_template(template['request_payload_template'], data)
            if isinstance(template.get('request_payload'), dict):
                template['request_payload'] = process_template(template['request_payload'], data)
                
            result = {}
            for key, value in template.items():
                # Process both keys and values recursively
                processed_key = process_template(key, data)
                processed_value = process_template(value, data)
                result[processed_key] = processed_value
            return result
            
        # Handle string templates with {{key}} pattern
        elif isinstance(template, str):
            # Find all {{key}} patterns in the string
            pattern = r'\{\{([^\}]+)\}\}'
            matches = re.findall(pattern, template)
            
            # Replace each match with the corresponding value from data
            result = template
            for match in matches:
                placeholder = '{{' + match + '}}'
                if match in data:
                    result = result.replace(placeholder, str(data[match]))
            return result
            
        # Return other types as is
        else:
            return template
            
    except Exception as e:
        print(f"Error processing template: {e}")
        traceback.print_exc()
        # Return the original template in case of error
        return template
