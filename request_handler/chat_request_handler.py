import sys
import os
import json
import traceback
import requests
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chat_request_handler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("chat_request_handler")

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import ChatRequest, ChatResponse
from rag_chain_builder import RAGChainBuilder
from langchain_core.prompts import ChatPromptTemplate
from database_v2 import get_ui_schema

# Load environment variables
load_dotenv()

# Determine which LLM to use based on environment variables or default to Ollama
LLM_TYPE = os.getenv("LLM_TYPE", "ollama").lower()  # "ollama" or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3" if LLM_TYPE == "ollama" else "gpt-3.5-turbo")

# Cache for UI components
_ui_schema_cache = None

def get_ui_components_by_id(ui_id):
    """
    Retrieve UI components by UI ID from the database
    
    Args:
        ui_id: The UI ID to look for
        
    Returns:
        The UI components structure or None if not found
    """
    global _ui_schema_cache
    
    # Initialize cache if needed
    if _ui_schema_cache is None:
        try:
            _ui_schema_cache = get_ui_schema()
            logger.info(f"Loaded {len(_ui_schema_cache)} UI schemas into cache")
        except Exception as e:
            logger.error(f"Error loading UI schemas: {e}")
            return None
    
    # Find the UI components by ID
    for schema in _ui_schema_cache:
        if schema.get("id") == ui_id:
            logger.info(f"Found UI components for ID: {ui_id}")
            return schema
    
    logger.warning(f"No UI components found for ID: {ui_id}")
    return None


def process_chat(request: ChatRequest):
    """
    Process a chat request and generate a response using the RAG chain.
    First translates any non-English input to English using translation_api.py.
    Then uses RAG to provide context info and UI components for the response.
    
    Args:
        request: The ChatRequest object containing the prompt and session information
        
    Returns:
        A dictionary containing the response and UI tags
    """
    # Initialize RAG chain builder at the beginning
    rag_chain_builder = RAGChainBuilder(llm_type=LLM_TYPE, model_name=LLM_MODEL)
    logger.info("Initialized RAG chain builder")
    
    prompt_text = request.prompt
    session_id = request.session_id
    chat_history = request.chat_history if hasattr(request, 'chat_history') and request.chat_history else []
    
    logger.info(f"Received chat request with prompt: '{prompt_text}' for session: {session_id}")
    
    if not prompt_text:
        logger.warning("Empty prompt received")
        return {"response": "Please provide a prompt or question.", "ui_tags": []}
    
    # First, pass the prompt to the translation API to handle non-English inputs
    try:
        translation_url = "http://localhost:8004/translate"  # Translation API endpoint
        logger.info(f"Sending prompt to translation API at {translation_url}")
        
        # Format chat history for translation API
        formatted_chat_history = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")} 
            for msg in chat_history
        ]
        
        # Prepare the request for translation service
        translation_request = {
            "tool": "chat",
            "type": "translation",
            "input": {
                "text": prompt_text, 
                "chat_history": formatted_chat_history
            }
        }
        logger.debug(f"Translation request: {json.dumps(translation_request)}")
        
        response = requests.post(translation_url, json=translation_request)
        logger.info(f"Translation API response status: {response.status_code}")
        
        if response.status_code == 200:
            translation_result = response.json()
            logger.debug(f"Translation result: {json.dumps(translation_result)}")
            
            # Extract information from translation API response
            input_data = translation_result.get("input", {})
            detected_lang = input_data.get("detected_lang")
            english_input = input_data.get("english_input", prompt_text)
            translated_response = input_data.get("translated_text")
            audio_response_path = input_data.get("audio_response_path")
            
            logger.info(f"Detected language: {detected_lang}")
            logger.info(f"NLP Layer Response - Full JSON: {json.dumps(translation_result)}")
            logger.info(f"NLP Layer Response - Detected Language: {detected_lang}")
            logger.info(f"NLP Layer Response - English Input: {english_input}")
            logger.info(f"NLP Layer Response - Translated Response: {translated_response}")
            logger.info(f"NLP Layer Response - Audio Path: {audio_response_path}")
            
            # If we got a translated response directly from the translation API
            if translated_response:
                logger.info(f"Using translated response from translation API")
                # The translation API already processed with get_gpt_response
                # We can now enrich this with RAG context
                # Get the English response from the translation API response
                english_response = english_input
                
                # Use the English response for RAG to fetch additional details
                try:
                    # Pass the English response to RAG system
                    logger.info(f"Passing English response to RAG: {english_response}")
                    # Use get_action_directly method for direct vector store lookup
                    rag_response = rag_chain_builder.get_action_directly(english_response)
                    
                    # If no direct match, use run_prompt_with_context with a simple prompt
                    if not rag_response:
                        logger.info("No direct match found, using prompt-based RAG")
                        simple_prompt = ChatPromptTemplate.from_messages([
                            ("system", "You are a helpful assistant. Provide information based on the context."),
                            ("human", "{query}")
                        ])
                        rag_response = rag_chain_builder.run_prompt_with_context(
                            query=english_response,
                            prompt=simple_prompt,
                            variables={"query": english_response}
                        )
                    logger.info(f"RAG response: {rag_response}")
                    
                    # Keep the RAG response as is (not stringified)
                    logger.info(f"RAG response: {rag_response}")
                    
                    # Extract action IDs from the RAG response if available
                    if isinstance(rag_response, dict):
                        action_id = rag_response.get("id")
                        next_success_action_id = rag_response.get("next_success_action_id")
                        next_err_action_id = rag_response.get("next_err_action_id")
                        title = rag_response.get("title", "")
                        ui_id = rag_response.get("ui_id")
                        
                        # Try to get UI components using the UI ID
                        ui_components = None
                        if ui_id:
                            logger.info(f"Looking up UI components for UI ID: {ui_id}")
                            ui_schema = get_ui_components_by_id(ui_id)
                            if ui_schema:
                                logger.info(f"Found UI schema for ID {ui_id}")
                                ui_components = ui_schema
                    else:
                        action_id = None
                        next_success_action_id = None
                        next_err_action_id = None
                        title = ""
                        ui_components = None
                    
                    # Keep the translated response as nlp_response and RAG response as the main response
                    response_data = {
                        "english_response": english_response,
                        "response": rag_response,  # RAG response as the main response
                        "nlp_response": translated_response,  # Translated response as nlp_response
                        "detected_language": detected_lang,
                        "audio_url": audio_response_path,
                        "ui_tags": ["translated_response", "rag_enriched"],
                        "id": action_id,
                        "next_success_action_id": next_success_action_id,
                        "next_err_action_id": next_err_action_id,
                        "title": title
                    }
                    
                    # Add UI components if available
                    if ui_components:
                        response_data["ui_components"] = ui_components
                        logger.info(f"Added UI components to response: {ui_components.get('id')}")
                    else:
                        logger.warning(f"No UI components found for UI ID: {ui_id if 'ui_id' in locals() else 'None'}")
                    
                except Exception as e:
                    logger.error(f"Error enriching response with RAG: {e}")
                    # Fallback to original response
                    response_data = {
                        "response": translated_response,
                        "english_response": english_response,
                        "detected_language": detected_lang,
                        "audio_url": audio_response_path,
                        "ui_tags": ["translated_response"]
                    }
                logger.info(f"Returning response from NLP layer: {json.dumps(response_data)}")
                return response_data
            
            # If we only got the English translation of the input
            if detected_lang != "english" and english_input:
                original_prompt = prompt_text
                prompt_text = english_input
                logger.info(f"Translated prompt from '{detected_lang}': '{original_prompt}' -> '{prompt_text}'")
        else:
            logger.error(f"Translation API error status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Translation API error: {str(e)}")
        logger.error(traceback.format_exc())
        # Continue with original prompt if translation fails
    
    # If we've reached here, we need to process with RAG
    # Either we have an English prompt or a translated prompt
    system_prompt = """
        You are an expert AI assistant for a loan onboarding application.
        Your task is to analyze the user's query, understand the semantic intent, and provide helpful information based on the retrieved context.
        
        **Context:**
        {context}
        
        **Instructions:**
        Based on the context above, provide a JSON object with the following keys:

        - "ui_components": The COMPLETE UI components structure from the context. This is very important - if you detect intent related to prospect information, customer data, or KYC, you MUST include the full UI component structure, not just references.
        - "id": action_id. If the user is asking about prospect info, use the corresponding prospect info ID.
        - "ui_id": ui_id. For prospect info or KYC related queries, use the appropriate ui_id (e.g., ui_prospect_info_001).
        - "screen_id": screen_id.
        - "type": type.
        - "title": add some suited text related to title.
        - next_success_action_id: The ID of the next action to be performed.
        - next_err_action_id: The ID of the next action to be performed.
        
        IMPORTANT INSTRUCTION FOR UI SCHEMAS:
        - When a user asks about prospect information, adding customer data, or KYC processes (even without mentioning exact IDs), you MUST return the complete UI schema with all components.
        - Do not just return a description or reference - return the ENTIRE ui_components structure as found in the context.
        - Match on semantic intent, not just explicit ID mentions. For example, "add prospect info", "secondary kyc", "customer information" should all retrieve the complete UI schema.
        
        Format your response in a clear, structured way that will be easy for the user to understand.
        If a piece of information is not available in the context, use a null value for that key.
        Only output the JSON object, with no additional text or explanation.
        
            "id": "user-details",
            "stage_name": "User Details Screen",
            "desc_for_llm": "User details collection screen for customer name and mobile number.",
            "action_type": "USER_DETAILS_SCREEN",
            "next_err_action_id": "details-error-screen",
            "next_success_action_id": "dashboard-screen",
            "ui_id": "ui_user_details_001",
            "api_detail_id": "api_user_details_001"
        
        
           "id": "ui_welcome_screen_001",
            "type": "UI",
            "session_id": "session_welcome_001",
            "screen_id": "welcome_screen",
            "ui_components":[]
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "i want to fetch ui_components, id related to id:{query}")
    ])
    
    try:
        # Initialize RAG builder with the configured LLM type and model
        logger.info(f"Using LLM type: {LLM_TYPE}, model: {LLM_MODEL}")
        rag_builder = RAGChainBuilder(llm_type=LLM_TYPE, model_name=LLM_MODEL)
        logger.info(f"Initializing RAGChainBuilder")
        
        # First try to get a direct action match from the vector store
        logger.info(f"Attempting direct action retrieval with prompt: '{prompt_text}'")
        direct_action = rag_builder.get_action_directly(prompt_text)
        
        if direct_action:
            logger.info(f"Found direct action match in vector store: {json.dumps(direct_action)}")
            
            # If we have a detected language that's not English, we need to translate the response back
            if 'detected_lang' in locals() and detected_lang and detected_lang.lower() != "english":
                try:
                    # Prepare to translate the response back to the original language
                    translation_request = {
                        "tool": "chat",
                        "type": "translation",
                        "input": {
                            "text": json.dumps(direct_action),
                            "target_lang": detected_lang
                        }
                    }
                    
                    # Call translation API to translate the response back
                    logger.info(f"Translating response back to {detected_lang}")
                    response = requests.post(translation_url, json=translation_request)
                    
                    if response.status_code == 200:
                        translation_result = response.json()
                        translated_response = translation_result.get("input", {}).get("translated_text")
                        audio_url = translation_result.get("input", {}).get("audio_response_path")
                        
                        if translated_response:
                            logger.info(f"Successfully translated response back to {detected_lang}")
                            # Get the English response for RAG
                            english_response = json.dumps(direct_action)
                            
                            try:
                                # Pass the English response to RAG system
                                logger.info(f"Passing English response to RAG: {english_response}")
                                # Use get_action_directly method for direct vector store lookup
                                rag_response = rag_chain_builder.get_action_directly(english_response)
                                
                                # If no direct match, use run_prompt_with_context with a simple prompt
                                if not rag_response:
                                    logger.info("No direct match found, using prompt-based RAG")
                                    simple_prompt = ChatPromptTemplate.from_messages([
                                        ("system", "You are a helpful assistant. Provide information based on the context."),
                                        ("human", "{query}")
                                    ])
                                    rag_response = rag_chain_builder.run_prompt_with_context(
                                        query=english_response,
                                        prompt=simple_prompt,
                                        variables={"query": english_response}
                                    )
                                
                                logger.info(f"RAG response: {rag_response}")
                                
                                # Combine the original response with RAG details
                            
                                # Extract action IDs from the direct action if available
                                if isinstance(direct_action, dict):
                                    action_id = direct_action.get("id")
                                    next_success_action_id = direct_action.get("next_success_action_id")
                                    next_err_action_id = direct_action.get("next_err_action_id")
                                    title = direct_action.get("title", "")
                                    ui_id = direct_action.get("ui_id")
                                    direct_action_str = json.dumps(direct_action)
                                    
                                    # Try to get UI components using the UI ID
                                    ui_components = None
                                    if ui_id:
                                        logger.info(f"Looking up UI components for UI ID: {ui_id}")
                                        ui_schema = get_ui_components_by_id(ui_id)
                                        if ui_schema:
                                            logger.info(f"Found UI schema for ID {ui_id}")
                                            ui_components = ui_schema
                                else:
                                    action_id = None
                                    next_success_action_id = None
                                    next_err_action_id = None
                                    title = ""
                                    ui_components = None
                                    direct_action_str = str(direct_action)
                                
                                # Create response data with all necessary fields
                                response_data = {
                                    "response": direct_action,  # Use direct_action as the main response (not stringified)
                                    "english_response": english_response,
                                    "nlp_response": translated_response,  # Use translated_response as nlp_response
                                    "detected_language": detected_lang,
                                    "audio_url": audio_url,
                                    "ui_tags": ["action_match", "direct_response", "translated"],
                                    "id": action_id,
                                    "next_success_action_id": next_success_action_id,
                                    "next_err_action_id": next_err_action_id,
                                    "title": title
                                }
                                
                                # Add UI components if available
                                if ui_components:
                                    response_data["ui_components"] = ui_components
                                    logger.info(f"Added UI components to response: {ui_components.get('id')}")
                                    response_data["ui_tags"].append("ui_components")
                                else:
                                    logger.warning(f"No UI components found for UI ID: {ui_id if 'ui_id' in locals() else 'None'}")
                            except Exception as e:
                                logger.error(f"Error enriching response with RAG: {e}")
                                # Extract action IDs from the direct action if available
                                if isinstance(direct_action, dict):
                                    action_id = direct_action.get("id")
                                    next_success_action_id = direct_action.get("next_success_action_id")
                                    next_err_action_id = direct_action.get("next_err_action_id")
                                    title = direct_action.get("title", "")
                                else:
                                    action_id = None
                                    next_success_action_id = None
                                    next_err_action_id = None
                                    title = ""
                                
                                # Create response data with all necessary fields
                                response_data = {
                                    "response": None,  # No direct action response due to error
                                    "english_response": english_response,
                                    "nlp_response": translated_response,  # Use translated_response as nlp_response
                                    "detected_language": detected_lang,
                                    "audio_url": audio_url,
                                    "ui_tags": ["action_match", "direct_response", "translated"],
                                    "id": action_id,
                                    "next_success_action_id": next_success_action_id,
                                    "next_err_action_id": next_err_action_id,
                                    "title": title
                                }
                            logger.info(f"Returning translated direct action response: {json.dumps(response_data)}")
                            return response_data
                except Exception as e:
                    logger.error(f"Error translating response back: {str(e)}")
                    # Fall back to English response if translation fails
            
            # Return the direct action match in English
            # Extract action IDs from the direct action if available
            if isinstance(direct_action, dict):
                action_id = direct_action.get("id")
                next_success_action_id = direct_action.get("next_success_action_id")
                next_err_action_id = direct_action.get("next_err_action_id")
                title = direct_action.get("title", "")
                ui_id = direct_action.get("ui_id")
                direct_action_str = json.dumps(direct_action)
                
                # Try to get UI components using the UI ID
                ui_components = None
                if ui_id:
                    logger.info(f"Looking up UI components for UI ID: {ui_id}")
                    ui_schema = get_ui_components_by_id(ui_id)
                    if ui_schema:
                        logger.info(f"Found UI schema for ID {ui_id}")
                        ui_components = ui_schema
            else:
                action_id = None
                next_success_action_id = None
                next_err_action_id = None
                title = ""
                ui_components = None
                direct_action_str = str(direct_action)
            
            # Create response data with all necessary fields
            response_data = {
                "response": direct_action,  # Use direct_action as the main response (not stringified)
                "english_response": direct_action_str,
                "nlp_response": direct_action_str,  # Use direct_action_str as nlp_response
                "detected_language": "english",
                "audio_url": None,
                "ui_tags": ["action_match", "direct_response"],
                "id": action_id,
                "next_success_action_id": next_success_action_id,
                "next_err_action_id": next_err_action_id,
                "title": title
            }
            
            # Add UI components if available
            if ui_components:
                response_data["ui_components"] = ui_components
                logger.info(f"Added UI components to response: {ui_components.get('id')}")
                response_data["ui_tags"].append("ui_components")
            else:
                logger.warning(f"No UI components found for UI ID: {ui_id if 'ui_id' in locals() else 'None'}")
            logger.info(f"Returning direct action response: {json.dumps(response_data)}")
            return response_data
        
        # If no direct match, use the RAG chain to generate a response
        logger.info("No direct action found, using RAG chain with system prompt")
        
        # Add the translated prompt to the chat history for context
        formatted_history = []
        for msg in chat_history:
            formatted_history.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        # Add the current prompt
        formatted_history.append({"role": "user", "content": prompt_text})
        
        # Get LLM response with RAG context
        llm_response = rag_builder.run_prompt_with_context(prompt_text, prompt)
        
        # Check if we got a valid response
        if not llm_response:
            logger.info("No valid response from LLM")
            return {
                "response": "I couldn't find a good answer to your question. Could you please rephrase or provide more details?",
                "ui_tags": ["no_context_found"]
            }
        
        # For non-English users, translate the response back to their language
        if 'detected_lang' in locals() and detected_lang and detected_lang.lower() != "english":
            try:
                # Prepare to translate the response back to the original language
                translation_request = {
                    "tool": "chat",
                    "type": "translation",
                    "input": {
                        "text": llm_response,
                        "target_lang": detected_lang
                    }
                }
                
                # Call translation API to translate the response back
                logger.info(f"Translating RAG response back to {detected_lang}")
                response = requests.post(translation_url, json=translation_request)
                
                if response.status_code == 200:
                    translation_result = response.json()
                    translated_response = translation_result.get("input", {}).get("translated_text")
                    audio_url = translation_result.get("input", {}).get("audio_response_path")
                    
                    if translated_response:
                        logger.info(f"Successfully translated RAG response back to {detected_lang}")
                        # Get the English response for RAG
                        english_response = llm_response
                        
                        try:
                            # Pass the English response to RAG system
                            logger.info(f"Passing English response to RAG: {english_response}")
                            # Use get_action_directly method for direct vector store lookup
                            rag_response = rag_chain_builder.get_action_directly(english_response)
                            
                            # If no direct match, use run_prompt_with_context with a simple prompt
                            if not rag_response:
                                logger.info("No direct match found, using prompt-based RAG")
                                simple_prompt = ChatPromptTemplate.from_messages([
                                    ("system", "You are a helpful assistant. Provide information based on the context."),
                                    ("human", "{query}")
                                ])
                                rag_response = rag_chain_builder.run_prompt_with_context(
                                    query=english_response,
                                    prompt=simple_prompt,
                                    variables={"query": english_response}
                                )
                            
                            # Extract action IDs from rag_response if it's a dict
                            if isinstance(rag_response, dict):
                                action_id = rag_response.get("id")
                                next_success_action_id = rag_response.get("next_success_action_id")
                                next_err_action_id = rag_response.get("next_err_action_id")
                                title = rag_response.get("title", "")
                            else:
                                action_id = None
                                next_success_action_id = None
                                next_err_action_id = None
                                title = ""
                            
                            logger.info(f"RAG response: {rag_response}")
                            
                            # Keep the translated response and RAG response separate
                            response_data = {
                                "response": translated_response,  # Just the translated response without RAG info
                                "response": rag_response,  # RAG response as the main response
                                "english_response": english_response,
                                "nlp_response": translated_response,  # Translated response as nlp_response
                                "detected_language": detected_lang,
                                "audio_url": audio_url,
                                "ui_tags": ["translated", "rag_enriched"],
                                "id": action_id,
                                "next_success_action_id": next_success_action_id,
                                "next_err_action_id": next_err_action_id,
                                "title": title
                            }
                        except Exception as e:
                            logger.error(f"Error enriching response with RAG: {e}")
                            # Fallback to original response
                            response_data = {
                                "response": None,  # No RAG response due to error
                                "english_response": english_response,
                                "nlp_response": translated_response,  # Use translated_response as nlp_response
                                "detected_language": detected_lang,
                                "audio_url": audio_url,
                                "ui_tags": ["translated"],
                                "id": None,
                                "next_success_action_id": None,
                                "next_err_action_id": None,
                                "title": ""
                            }
                        logger.info(f"Returning translated RAG response: {json.dumps(response_data)}")
                        return response_data
            except Exception as e:
                logger.error(f"Error translating RAG response back: {str(e)}")
                # Fall back to English response if translation fails
       
        # Return the English response if no translation was needed or if translation failed
        try:
            # Try to get RAG response for the English text
            rag_response = rag_chain_builder.get_action_directly(llm_response)
            
            # If no direct match, use run_prompt_with_context with a simple prompt
            if not rag_response:
                logger.info("No direct match found, using prompt-based RAG")
                simple_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant. Provide information based on the context."),
                    ("human", "{query}")
                ])
                rag_response = rag_chain_builder.run_prompt_with_context(
                    query=llm_response,
                    prompt=simple_prompt,
                    variables={"query": llm_response}
                )
            
            # Extract action IDs and UI ID from the RAG response if available
            if isinstance(rag_response, dict):
                action_id = rag_response.get("id")
                next_success_action_id = rag_response.get("next_success_action_id")
                next_err_action_id = rag_response.get("next_err_action_id")
                title = rag_response.get("title", "")
                ui_id = rag_response.get("ui_id")
                
                # Try to get UI components using the UI ID
                ui_components = None
                if ui_id:
                    logger.info(f"Looking up UI components for UI ID: {ui_id}")
                    ui_schema = get_ui_components_by_id(ui_id)
                    if ui_schema:
                        logger.info(f"Found UI schema for ID {ui_id}")
                        ui_components = ui_schema
            else:
                action_id = None
                next_success_action_id = None
                next_err_action_id = None
                title = ""
                ui_components = None
                
            logger.info(f"RAG response for English: {rag_response}")
            
            # Construct the response data
            response_data = {
                "response": rag_response,  # Use rag_response as the main response (not stringified)
                "english_response": llm_response,  # Set english_response to the original response
                "nlp_response": llm_response,  # Use llm_response as nlp_response
                "detected_language": "english",
                "audio_url": None,
                "ui_tags": ["rag_enriched"],
                "id": action_id,
                "next_success_action_id": next_success_action_id,
                "next_err_action_id": next_err_action_id,
                "title": title
            }
            
            # Add UI components if available
            if ui_components:
                response_data["ui_components"] = ui_components
                logger.info(f"Added UI components to response: {ui_components.get('id')}")
                response_data["ui_tags"].append("ui_components")
            else:
                logger.warning(f"No UI components found for UI ID: {ui_id if 'ui_id' in locals() else 'None'}")
                
            logger.info(f"Returning English RAG response: {json.dumps(response_data)}")
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting RAG response for English: {e}")
            response_data = {
                "response": None,  # No RAG response due to error
                "english_response": llm_response,  # Set english_response to the original response
                "nlp_response": llm_response,  # Use llm_response as nlp_response
                "detected_language": "english",
                "audio_url": None,
                "ui_tags": [],
                "id": None,
                "next_success_action_id": None,
                "next_err_action_id": None,
                "title": ""
            }
        
        logger.info(f"Returning English RAG response: {json.dumps(response_data)}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in process_chat: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "response": f"An error occurred while processing your request: {str(e)}",
            "ui_tags": ["error"]
        }


def extract_entities(text: str):
    """
    Extract named entities from the chat text that might be relevant for tagging or categorization.
    
    Args:
        text: The text to analyze
        
    Returns:
        A list of extracted entities and their types
    """
    try:
        # This is a placeholder for more sophisticated entity extraction
        # In a production system, you might use NER models or more complex logic
        entities = []
        
        # Simple keyword matching for common loan-related terms
        keywords = {
            "loan": "product",
            "mortgage": "product",
            "interest": "attribute",
            "rate": "attribute",
            "application": "process",
            "document": "requirement",
            "credit": "attribute",
            "approval": "status",
            "payment": "process"
        }
        
        # Check for keywords in the text
        for keyword, entity_type in keywords.items():
            if keyword.lower() in text.lower():
                entities.append({"text": keyword, "type": entity_type})
        
        return entities
    except Exception as e:
        print(f"Error extracting entities: {str(e)}")
        return []