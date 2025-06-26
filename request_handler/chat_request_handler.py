import sys
import os
import json
import traceback
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import ChatRequest, ChatResponse
from rag_chain_builder import RAGChainBuilder
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Determine which LLM to use based on environment variables or default to Ollama
LLM_TYPE = os.getenv("LLM_TYPE", "ollama").lower()  # "ollama" or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3" if LLM_TYPE == "ollama" else "gpt-3.5-turbo")


def process_chat(chat_request: ChatRequest):
    """
    Process a chat request and return a response with UI components and action details.
    
    Args:
        chat_request: ChatRequest object containing the user's prompt and session_id
        
    Returns:
        dict: Response containing the LLM response and UI tags
    """
    
    prompt_text = chat_request.prompt.strip()
    
    if not prompt_text:
        return {"response": "Please provide a prompt or question.", "ui_tags": []}
    
    # Use the same comprehensive system prompt as submit handler to ensure complete action structure
    system_prompt = """
        You are a UI component and workflow extractor. Your task is to extract specific information from the provided context and return a complete action structure.
        
        CRITICAL INSTRUCTIONS:
        1. Extract the current action's UI components from the context
        2. Find the next_success_action_id for the current action
        3. Extract ONLY the UI components that belong to the next_success_action_id - DO NOT include multiple UI schemas
        4. NEVER hallucinate or substitute values - copy all properties and URLs exactly as they appear
        5. NEVER use placeholder values like "example.com" - use the exact URLs from the source data
        6. PRESERVE ALL ORIGINAL TEXT VALUES - do not modify titles, headings, or any text content
        7. Temperature is set to 0 - be deterministic and precise
        
        TITLE AND TEXT PRESERVATION RULES:
        - If a UI component has a "title" field, copy it EXACTLY as it appears in the source
        - If a text component has a "text" property, copy it EXACTLY without modification
        - DO NOT generate descriptive titles like "UI Components related to..." - use original values only
        - DO NOT rephrase, summarize, or modify any text content from the source data
        - The title field is displayed to end users in the frontend - it must be the original value
        
        REQUIRED OUTPUT STRUCTURE:
        You must return a JSON object with the following structure:
        {{
            "ui_components": [array of UI components for current action],
            "id": "action-id",
            "ui_id": "ui_action_id_001", 
            "screen_id": "action-screen-id",
            "type": "action",
            "title": "Action Title (exactly as in source)",
            "next_success_action_id": "next-action-id",
            "next_err_action_id": "error-action-id"
        }}
        
        STEP-BY-STEP EXTRACTION PROCESS:
        1. Identify the current action and its complete metadata
        2. Extract all UI components for the current action
        3. Find the next_success_action_id and next_err_action_id from the action metadata
        4. Copy the action's id, ui_id, screen_id, type, and title exactly as they appear
        5. Ensure all text values and properties are copied EXACTLY from the source
        
        VALIDATION RULES:
        - ALL text content must be copied exactly from source data without modification
        - Include all required fields: id, ui_id, screen_id, type, title, next_success_action_id, next_err_action_id
        - ui_components must be an array containing the complete UI schema for the current action
        
        Context: {context}
        Query: {query}
        
        Return the complete action structure as JSON:
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "i want to fetch ui_components, id related to id:{query}")
    ])
    
    try:
        # Initialize RAG builder with the configured LLM type and model
        rag_builder = RAGChainBuilder(llm_type=LLM_TYPE, model_name=LLM_MODEL)
        print(f"Using {LLM_TYPE} model {LLM_MODEL} for processing chat prompt: {prompt_text[:50]}...")
        
        # First try to get a direct action match from the vector store
        # direct_action = rag_builder.get_action_directly(prompt_text)
        # if direct_action:
        #     print("Found direct action match in vector store")
        #     return {
        #         "response": direct_action,
        #         "ui_tags": ["action_match", "direct_response"]
        #     }
        
        # If no direct match, use the RAG chain to generate a response
        llm_response = rag_builder.run_prompt_with_context(prompt_text, prompt)
        
        # Check if we got a valid response
        if not llm_response:
            print("No valid response from LLM")
            return {
                "response": "I couldn't find a good answer to your question. Could you please rephrase or provide more details?",
                "ui_tags": ["no_context_found"]
            }
        
       
        return {
            "response": llm_response,
        }
        
    except Exception as e:
        print(f"Error in process_chat: {str(e)}")
        traceback.print_exc()
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