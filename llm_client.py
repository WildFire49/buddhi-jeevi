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
