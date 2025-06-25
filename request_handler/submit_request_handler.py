import sys
import os
import json
import re
import traceback
from dotenv import load_dotenv
import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import DataSubmitRequest, DataSubmitResponse, KeyValuePair
from rag_chain_builder import RAGChainBuilder
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Determine which LLM to use based on environment variables or default to Ollama
LLM_TYPE = os.getenv("LLM_TYPE", "ollama").lower()  # "ollama" or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3" if LLM_TYPE == "ollama" else "gpt-3.5-turbo")


def submit_data(request: DataSubmitRequest):
    action_id = request.action_id
    if not action_id:
        print("No action_id provided in request")
        return []
    
    system_prompt = """
        You are an expert system that processes retrieved data about an application's workflow.
        Your task is to analyze the provided context and extract specific information in a structured JSON format.

        **Context:**
        {context}

        **Instructions:**
        Based on the context above, provide a JSON object with the following keys:
        - "ui_components": The UI components associated with the action.
        - "api_details": The API endpoint details for the action.
        - "next_action_id": The ID of the next action to be performed.
        - based on the next_action_id also return ui_components for next_action
        
        Critical Instruction: Unique ID Generation
        For every UI component found within "ui_components" and "next_action_ui_components", you must generate a new, unique "id".

        The generated "id" must be a string formatted as: {current_epoch_timestamp}_descriptive_name.

        {current_epoch_timestamp}: Generate the current Unix epoch timestamp.

        descriptive_name: Create this name by using existing value which you have to update

        Examples of how to generate IDs:

        If a component is a button with the label "Submit Application", its generated ID should be similar to: "1719331800_submit_application_button"

        If a component is an input field with the placeholder "Enter your first name", its generated ID should be similar to: "1719331800_enter_your_first_name_input"

        If a component is a title with the text "Login Page", its generated ID should be similar to: "1719331800_login_page_title"


        Only output the JSON object, with no additional text or explanation.
        """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Process the context for the action related to this query: {query}")
    ])

    try:
        # Initialize RAG builder with the configured LLM type and model
        rag_builder = RAGChainBuilder(llm_type=LLM_TYPE, model_name=LLM_MODEL)
        print(f"Using {LLM_TYPE} model {LLM_MODEL} for processing action_id: {action_id}")
        current_timestamp_str = datetime.datetime.now().strftime("%d%m%H%M%S")

        # Get the response from the LLM as a dictionary
        llm_response = rag_builder.run_prompt_with_context(
            action_id, prompt, {"current_timestamp": current_timestamp_str}
        )
        if not llm_response or not isinstance(llm_response, dict):
            print(f"No valid response from LLM: {llm_response}")
            return {}
        
        # Extract components from the LLM response dictionary
        ui_components = llm_response.get('ui_components', [])
        api_details = llm_response.get('api_details', [])
        next_action_id = llm_response.get('next_action_id')
        next_action_ui_components = llm_response.get('next_action_ui_components', [])
        
        data = request.data
        response = api_executor(api_details, data)
        print("api_executor", response)
        # Process results into the expected format
        processed_results = {
            "ui_components": next_action_ui_components,
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
                    converted_data[item.key] = item.value
                elif isinstance(item, dict) and 'key' in item and 'value' in item:
                    # Fallback for dictionary format
                    converted_data[item['key']] = item['value']
    
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
