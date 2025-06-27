import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings # New import for OpenAI embeddings
from langchain_huggingface import HuggingFaceEmbeddings # Import for fallback embeddings
from langchain_chroma import Chroma
import chromadb

# Load environment variables
load_dotenv()

class VectorDBTools:
    """
    A class providing tools for interacting with the vector database.
    """
    
    def __init__(self):
        """
        Initialize the VectorDBTools with necessary components.
        """
        print("Initializing VectorDBTools components...")
        
        # Try to initialize embeddings with error handling and fallbacks
        try:
            
            openai_api_key = os.getenv("OPENAI_API_KEY")

            # Try to initialize with the specified model
            self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="nomic-embed-text")

            print("Initialized OpenAI  embeddings successfully")
        
        except Exception as e:
            print(f"Error initializing primary embeddings model: {e}")
            print("Trying alternative embedding model...")
            
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            cache_folder = "./.embeddings_cache"
            
            # Check if we have a local copy of the model in the cache folder
            if os.path.exists(os.path.join(cache_folder, model_name.replace('/', '_'))):
                print(f"Using locally cached model from {cache_folder}")
            else:
                print(f"Model not found in {cache_folder}, will try to download")
            
            try:
                
                # Try a different model as fallback
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="distilbert-base-uncased",
                    cache_folder="./.embeddings_cache"
                )
                print("Initialized fallback embeddings model")
            except Exception as e2:
                print(f"Error initializing fallback embeddings model: {e2}")
                raise RuntimeError("Failed to initialize any embedding models. Please ensure internet connectivity or pre-download the models.") from e2
        
        # Initialize Chroma vector store with onboarding_flow collection
        try:
            self.vector_store = Chroma(
                collection_name="onboarding_flow_15",
                embedding_function=self.embeddings,
                client=chromadb.HttpClient(
                    host="3.6.132.24",
                    port=8000
                )
            )
            print("VectorDBTools initialized successfully")
        except Exception as e:
            print(f"Error connecting to Chroma DB: {e}")
            raise RuntimeError("Failed to connect to vector database. Please check your connection and credentials.") from e
    
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
                where={"ids": action_id}
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