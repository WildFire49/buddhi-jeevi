import os
from typing import Dict, List

from openai import OpenAI


class OllamaClient:
    """
    A client for interacting with a local Ollama-served model using the
    OpenAI-compatible API.

    Configuration is loaded from environment variables but falls back to defaults
    if they are not set.
    """
    _instance = None  # Class variable to hold the single instance

    def __init__(self):
        """
        Initializes the Ollama client.
        """
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        # The API key is required by the OpenAI library but not used by Ollama.
        api_key = "ollama"

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def __new__(cls):
        """
        Ensures that only one instance of OllamaClient is created.
        """
        if cls._instance is None:
            cls._instance = super(OllamaClient, cls).__new__(cls)
            # Initialize the instance only once when it's first created
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        """
        Internal method to perform the actual client initialization.
        This ensures the client is set up only once.
        """
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        api_key = "ollama"  # required, but unused by Ollama
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def get_completion(self, messages: List[Dict[str, str]], model: str = "llama3") -> str:
        """
        Gets a chat completion from the specified Ollama model.

        Args:
            messages: A list of messages in the OpenAI format (e.g., [{"role": "user", "content": "..."}]).
            model: The name of the model to use (e.g., 'llama3').

        Returns:
            The content of the model's response message as a string.
        """
        chat_completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return chat_completion.choices[0].message.content or ""

# Create a single, reusable instance of the client to be imported by other modules.
ollama_client = OllamaClient()