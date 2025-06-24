import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb

# Load environment variables
load_dotenv()

class VectorDBTools:
    """
    A class providing tools for interacting with the vector database.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern implementation to ensure only one instance of VectorDBTools exists.
        """
        if not cls._instance:
            print("Creating a new VectorDBTools instance...")
            cls._instance = super(VectorDBTools, cls).__new__(cls)
        else:
            print("Returning existing VectorDBTools instance...")
        return cls._instance
    
    def __init__(self):
        """
        Initialize the VectorDBTools with ChromaDB connection.
        """
        # The hasattr check prevents re-initialization on subsequent calls
        if not hasattr(self, 'is_initialized'):
            # Initialize ChromaDB client
            self.client = chromadb.HttpClient(host='3.6.132.24', port=8000)
            
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model="text-embedding-3-small"
            )
            
            # Initialize Chroma vector store with onboarding_flow collection
            self.vector_store = Chroma(
                client=self.client,
                collection_name="onboarding_flow",
                embedding_function=self.embeddings
            )
            
            self.is_initialized = True
            print("VectorDBTools initialized successfully")
    
    def search_by_action_id(self, action_id: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector database for documents matching a specific action_id.
        
        Args:
            action_id (str): The action ID to search for
            k (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching documents with their metadata
        """
        try:
            # First try an exact metadata filter search
            results = self.vector_store.get(
                where={"action_id": action_id}
            )
            
            if results and len(results['ids']) > 0:
                # Format the results
                formatted_results = []
                for i in range(len(results['ids'])):
                    formatted_results.append({
                        "id": results['ids'][i],
                        "content": results['documents'][i] if 'documents' in results else None,
                        "metadata": results['metadatas'][i] if 'metadatas' in results else {}
                    })
                return formatted_results
            
            # If no exact match, try a similarity search with the action_id as query
            results = self.vector_store.similarity_search(
                query=f"action {action_id}",
                k=k
            )
            
            # Format the results from similarity search
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "id": getattr(doc, "id", None),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching vector database: {e}")
            return []
    
    def search_by_text(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector database for documents matching a text query.
        
        Args:
            query (str): The text query to search for
            k (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching documents with their metadata
        """
        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=k
            )
            
            # Format the results
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "id": getattr(doc, "id", None),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching vector database: {e}")
            return []
