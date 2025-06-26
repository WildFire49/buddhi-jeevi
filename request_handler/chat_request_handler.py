import sys
import os
import json
import traceback
import requests
import logging
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import ChatRequest, ChatResponse
from rag_chain_builder import RAGChainBuilder
from langchain_core.prompts import ChatPromptTemplate
from request_handler.mcp_agent_handler import MCPAgentHandler

# Load environment variables
load_dotenv()

# Determine which LLM to use based on environment variables or default to Ollama
LLM_TYPE = os.getenv("LLM_TYPE", "ollama").lower()  # "ollama" or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3" if LLM_TYPE == "ollama" else "gpt-3.5-turbo")


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP agent handler
mcp_agent_handler = MCPAgentHandler()

def process_chat(request: ChatRequest):
    """
    Process a chat request and generate a response using either the RAG chain or MCP agent.
    Intelligently routes between workflow steps and dashboard metrics based on query context.
    
    Args:
        request: The ChatRequest object containing the prompt and session information
        
    Returns:
        A dictionary containing the response and UI tags
    """
    prompt_text = request.prompt
    session_id = request.session_id or "default-session"
    
    if not prompt_text:
        logger.warning("No prompt provided in request")
        return {"response": "Please provide a prompt or question.", "ui_tags": []}
    
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
        # First check if this should be routed to the MCP dashboard agent
        if mcp_agent_handler.should_route_to_mcp_agent(prompt_text):
            logger.info(f"Routing query to MCP agent: {prompt_text}")
            
            # Prepare custom metadata based on query content if needed
            metadata = None
            
            # Extract query-specific metadata that might be useful to the agent
            # This allows for dynamic, context-aware metadata construction
            if any(term in prompt_text.lower() for term in ["credit", "loan", "borrower", "approval"]):
                metadata = {
                    "queryCategory": "credit_decision",
                    "includeRiskMetrics": True
                }
            elif any(term in prompt_text.lower() for term in ["report", "pdf", "export", "document"]):
                metadata = {
                    "format": "pdf",
                    "includeCharts": True
                }
            
            # Process through MCP agent handler with optional metadata
            mcp_response = mcp_agent_handler.process_query(prompt_text, session_id, metadata)
            
            # If successfully routed to MCP, return the appropriate data
            if mcp_response.get("routed_to_mcp") and mcp_response.get("status") == "success":
                logger.info(f"Successfully retrieved data from MCP agent: {mcp_response.get('agent_name')}")
                
                # Customize response based on agent type
                agent_name = mcp_response.get("agent_name", "mcp_agent")
                response_message = "Data retrieved"
                ui_tags = ["mcp_data"]
                action_id = "mcp_view"
                
                if "dashboard" in agent_name:
                    response_message = "Dashboard data retrieved"
                    ui_tags = ["dashboard_data"]
                    action_id = "dashboard_view"
                elif "credit" in agent_name:
                    response_message = "Credit evaluation retrieved"
                    ui_tags = ["credit_data"]
                    action_id = "credit_view"
                elif "reporting" in agent_name:
                    response_message = "Report generated"
                    ui_tags = ["report_data"]
                    action_id = "report_view"
                
                # Format response for the client
                return {
                    "response": {
                        "message": response_message,
                        "data": mcp_response.get("data", {}),
                        "source": agent_name
                    },
                    "ui_tags": ui_tags,
                    "session_id": session_id,
                    "action_id": action_id
                }
            else:
                # If there was an error with the MCP agent, log it but continue with normal processing
                logger.warning(f"MCP agent routing failed: {mcp_response.get('message')}, falling back to regular workflow")
        
        # If not routed to MCP or MCP failed, proceed with normal RAG processing
        logger.info(f"Processing query through workflow RAG: {prompt_text}")
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