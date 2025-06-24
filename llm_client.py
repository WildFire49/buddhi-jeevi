import operator
import json
import os
from typing import TypedDict, Annotated, List, Dict, Any, Union, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangChain and LangGraph imports
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# --- 1. OpenAI Integration as a Class ---

class LLMManager:
    """
    A dedicated class to manage the connection and interaction with the OpenAI LLM.
    This encapsulates model loading and chain creation logic.
    """
    def __init__(self, model_name="gpt-3.5-turbo"):
        """
        Initializes the OpenAI Chat Model instance.
        This is done once to avoid reloading the model on every call.
        
        Args:
            model_name (str): The name of the model to use from OpenAI (e.g., 'gpt-3.5-turbo', 'gpt-4').
        """
        print(f"---LLMManager: Initializing model '{model_name}'---")
        # Initialize OpenAI model with API key from environment
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def get_intent_classifier_chain(self):
        """
        Builds and returns a LangChain runnable to classify user intent.
        
        Returns:
            A LangChain runnable object.
        """
        # Define the prompt template with clear instructions and examples.
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", 
                 "You are an expert at classifying user intent for a banking onboarding system. "
                 "Your goal is to determine the user's primary goal from their message. "
                 "You must classify the intent into one of the following predefined categories:\n"
                 " - login: If the user wants to log in, sign in, or start their workday.\n"
                 " - start_onboarding: If the user wants to begin a new customer application, add a customer, or onboard a new person.\n"
                 " - general_question: For any other question, greeting, or unclear request.\n"
                 "Respond with only the category name and nothing else."),
                ("human", "{user_input}")
            ]
        )

        # Create the chain by piping the components together.
        return prompt_template | self.llm | StrOutputParser()

# --- 2. Mock Data and Tools ---

def get_mock_vector_db():
    """Mocks a Vector DB containing our 'smart action' documents."""
    return {
        "JLG_S0_A1_LOGIN": {
            "action_id": "JLG_S0_A1_LOGIN",
            "stage_name": "Authentication",
            "ui_definition": {
                "step_title": "Officer Login",
                "bot_message": "Welcome. Please log in to continue.",
                "form_fields": [
                    {"field_id": "employeeId", "component_type": "Text Input Field", "properties": {"label": "Employee ID", "required": True}},
                    {"field_id": "password", "component_type": "Password Field", "properties": {"label": "Password", "required": True}}
                ],
                "submit_button": {"text": "Login"}
            }
        },
        "JLG_S1_A1_CAPTURE_AADHAAR": {
            "action_id": "JLG_S1_A1_CAPTURE_AADHAAR",
            "stage_name": "EKYC & ID Generation",
            "ui_definition": {
                "step_title": "Aadhar Verification",
                "bot_message": "Let's begin onboarding a new customer. Please enter their 12-digit Aadhar number.",
                "form_fields": [
                    {"field_id": "aadharNumber", "component_type": "Number Input Field", "properties": {"label": "Aadhar Number", "required": True, "validation_pattern": "^[2-9]\\d{11}$"}}
                ],
                "submit_button": {"text": "Verify Aadhar"}
            }
        }
    }

# --- 3. Define the State for the Graph ---

class OnboardingState(TypedDict):
    """Defines the state or 'memory' of our conversational agent."""
    messages: Annotated[List[BaseMessage], operator.add]
    user_intent: str
    ui_to_display: Optional[Dict[str, Any]]

# --- 4. Define the Nodes of the Graph ---

# Instantiate the LLM Manager once. This object will be used by the node.
llm_manager = LLMManager(model_name="gpt-3.5-turbo")

def classify_intent_node(state: OnboardingState):
    """
    This node uses the LLMManager to classify the user's intent.
    """
    print("---NODE: Classifying Intent---")
    last_message = state['messages'][-1]
    user_input = last_message.content
    
    # Get the pre-compiled chain from our manager instance
    intent_chain = llm_manager.get_intent_classifier_chain()
    
    # Invoke the chain
    intent = intent_chain.invoke({"user_input": user_input})
    print(f"  > Detected Intent: {intent}")
    
    return {"user_intent": intent}

def fetch_ui_node(state: OnboardingState):
    """
    This node fetches the UI definition from the mock DB based on the intent.
    """
    print("---NODE: Fetching UI---")
    intent = state.get("user_intent")
    
    action_id_to_fetch = ""
    if intent == "login":
        action_id_to_fetch = "JLG_S0_A1_LOGIN"
    elif intent == "start_onboarding":
        action_id_to_fetch = "JLG_S1_A1_CAPTURE_AADHAAR"
    else:
        return {"ui_to_display": {"bot_message": "I'm not sure how to help with that. Please try logging in or starting a new onboarding."}}
        
    print(f"  > Action ID to fetch from DB: {action_id_to_fetch}")
    
    vector_db = get_mock_vector_db()
    action_document = vector_db.get(action_id_to_fetch)
    
    if not action_document:
        return {"ui_to_display": {"bot_message": "Sorry, I can't find that flow."}}

    ui_definition = action_document.get("ui_definition")
    
    return {"ui_to_display": ui_definition}


# --- 5. Build and Compile the Graph ---

workflow = StateGraph(OnboardingState)
workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("fetch_ui", fetch_ui_node)
workflow.set_entry_point("classify_intent")
workflow.add_edge("classify_intent", "fetch_ui")
workflow.add_edge("fetch_ui", END)
app = workflow.compile()

# Optional: Visualize the graph
try:
    img_data = app.get_graph().draw_png()
    with open("graph.png", "wb") as f:
        f.write(img_data)
    print("\nGraph visualization saved to graph.png")
except Exception as e:
    print(f"Could not create graph visualization: {e}")


# --- 6. Run the Graph with User Input ---

if __name__ == "__main__":
    print("\n--- Running Scenario 1: User wants to start onboarding ---")
    print("    (Ensure your OpenAI API key is set in the environment)")
    
    user_input = "I want to add a new customer to the system."
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    final_state = app.invoke(initial_state)
    
    print("\n--- FINAL STATE ---")
    print(json.dumps(final_state.get("ui_to_display"), indent=2))

    print("\n" + "="*50 + "\n")

    print("--- Running Scenario 2: User wants to log in ---")
    
    user_input_2 = "Time to sign in and start my work."
    initial_state_2 = {"messages": [HumanMessage(content=user_input_2)]}
    final_state_2 = app.invoke(initial_state_2)
    
    print("\n--- FINAL STATE ---")
    print(json.dumps(final_state_2.get("ui_to_display"), indent=2))
