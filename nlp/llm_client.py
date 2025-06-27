
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force reload environment variables
load_dotenv(override=True)

# Get API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")

# Print the API key (first few characters) for debugging
if openai_api_key:
    masked_key = openai_api_key[:4] + "*" * (len(openai_api_key) - 8) + openai_api_key[-4:]
    logger.info(f"Using OpenAI API key: {masked_key}")
else:
    logger.error("OPENAI_API_KEY environment variable not set for OpenAI client.")
    # Use a fallback mechanism or dummy client for development
    openai_api_key = "dummy_key_for_development"

# Initialize the OpenAI client
try:
    client = OpenAI(api_key=openai_api_key)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}")
    # Create a dummy client that will be replaced with proper error handling in get_gpt_response
    client = None



def get_gpt_response(history):
    # If client is not initialized, return a fallback response
    if client is None:
        logger.error("OpenAI client not initialized. Using fallback response.")
        return "I'm sorry, but I'm having trouble connecting to my language model. Please check your API key configuration and try again later."
    
    # Joint loan process system prompt
    joint_loan_system_prompt = """
    You are a helpful assistant for a joint loan application process. 
    
    JOINT LOAN PROCESS CONTEXT:
    You are assisting users through a joint loan application process. This process involves multiple steps:
    1. Initial Application: Collecting basic information about both applicants
    2. Identity Verification: KYC process for both primary and secondary applicants
    3. Income Documentation: Uploading income proof for both applicants
    4. Credit Check: Consent and processing of credit checks
    5. Loan Terms Selection: Choosing loan amount, tenure, and interest rate
    6. Final Review: Reviewing all information before submission
    7. Digital Signature: Signing the loan agreement
    8. Approval Process: Waiting for loan approval
    
    When responding to user queries about the joint loan process:
    - Identify which step of the process they are referring to
    - Provide clear, numbered steps for what they need to do next
    - Reference both applicants when relevant (primary and secondary)
    - Include information about required documentation for each step
    - Keep your answers brief and to the point
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=300, 
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": joint_loan_system_prompt
                }
            ] + [
                {
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}]
                } for msg in history
            ]
        )
        
        # Handle both new (list-based) and old (string) formats
        content = response.choices[0].message.content
        if isinstance(content, list):
            return content[0]["text"]
        return content  # it's already a plain string
    except Exception as e:
        logger.error(f"Error getting GPT response: {e}")
        return "I'm sorry, but I'm having trouble connecting to my language model. Please check your API key configuration and try again later."
