import operator
import json
import os
from typing import TypedDict, Annotated, List, Dict, Any, Union, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangChain and LangGraph imports
import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Load environment variables from .env file
load_dotenv()

# Base LLM Manager class
class BaseLLMManager:
    """Base class for LLM managers"""
    def __init__(self):
        self.llm = None

# --- 1. Ollama (Llama 3) Integration ---
class OllamaLLMManager(BaseLLMManager):
    """
    A dedicated class to manage the connection and interaction with the Ollama LLM.
    This encapsulates model loading and chain creation logic.
    """
    def __init__(self, model_name="llama3"):
        """
        Initializes the Ollama Chat Model instance.
        This is done once to avoid reloading the model on every call.
        
        Args:
            model_name (str): The name of the model to use from Ollama (e.g., 'llama3', 'llama3:8b').
        """
        super().__init__()
        print(f"---OllamaLLMManager: Initializing Ollama model '{model_name}'---")
        # Initialize Ollama model
        self.llm = ChatOllama(
            model=model_name,
            temperature=0,
            base_url="http://localhost:11434"  # Default Ollama server URL
        )

# --- 2. OpenAI Integration ---
class OpenAILLMManager(BaseLLMManager):
    """
    A dedicated class to manage the connection and interaction with OpenAI models.
    This encapsulates model loading and chain creation logic.
    """
    def __init__(self, model_name="gpt-3.5-turbo"):
        """
        Initializes the OpenAI Chat Model instance.
        This is done once to avoid reloading the model on every call.
        
        Args:
            model_name (str): The name of the model to use from OpenAI (e.g., 'gpt-3.5-turbo', 'gpt-4').
        """
        super().__init__()
        # Get API key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            
        print(f"---OpenAILLMManager: Initializing OpenAI model '{model_name}'---")
        # Initialize OpenAI model
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key
        )

# Default LLM Manager (for backward compatibility)
class LLMManager(OllamaLLMManager):
    """Default LLM Manager that uses Ollama for backward compatibility"""
    pass
