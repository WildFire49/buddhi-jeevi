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
            # First try an exact metadata filter search for action schema
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
                        "metadata": results['metadatas'][i] if 'metadatas' in results else {},
                        "schema_type": "action"
                    })
                
                # Now look for related UI schema
                action_metadata = results['metadatas'][0] if results['metadatas'] else {}
                ui_id = action_metadata.get('ui_id')
                if ui_id:
                    ui_results = self.vector_store.get(
                        where={"ui_id": ui_id}
                    )
                    if ui_results and len(ui_results['ids']) > 0:
                        for i in range(len(ui_results['ids'])):
                            formatted_results.append({
                                "id": ui_results['ids'][i],
                                "content": ui_results['documents'][i] if 'documents' in ui_results else None,
                                "metadata": ui_results['metadatas'][i] if 'metadatas' in ui_results else {},
                                "schema_type": "ui"
                            })
                
                # Look for related API schema
                api_id = action_metadata.get('api_detail_id')
                if api_id:
                    api_results = self.vector_store.get(
                        where={"api_detail_id": api_id}
                    )
                    if api_results and len(api_results['ids']) > 0:
                        for i in range(len(api_results['ids'])):
                            formatted_results.append({
                                "id": api_results['ids'][i],
                                "content": api_results['documents'][i] if 'documents' in api_results else None,
                                "metadata": api_results['metadatas'][i] if 'metadatas' in api_results else {},
                                "schema_type": "api"
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
                schema_type = "unknown"
                if "type" in doc.metadata:
                    schema_type = doc.metadata["type"]
                elif "action_id" in doc.metadata:
                    schema_type = "action"
                elif "ui_id" in doc.metadata:
                    schema_type = "ui"
                elif "api_detail_id" in doc.metadata:
                    schema_type = "api"
                
                formatted_results.append({
                    "id": getattr(doc, "id", None),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "schema_type": schema_type
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
# if __name__ == '__main__':
#     res1 = VectorDBTools().search_by_action_id('JLG_S0_A3_MARK_ATTENDANCE_API')
#     # res2 = VectorDBTools().search_by_text('JLG_S0_A1_LOGIN')
#     print(res1)
    # print(res2)