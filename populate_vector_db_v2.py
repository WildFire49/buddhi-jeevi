import json
import os
import logging
import numpy as np
import chromadb
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from database_v2 import get_action_schema, get_ui_schema, get_api_schema

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Wrapper class for embedding models to match ChromaDB's interface
class ChromaEmbeddingWrapper:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
    
    def __call__(self, input):
        """ChromaDB expects __call__ with (self, input) signature and numpy arrays as output"""
        if isinstance(input, str):
            input = [input]
        # Get embeddings as list of floats
        embeddings = self.embedding_model.embed_documents(input)
        # Convert to numpy arrays as required by ChromaDB
        return [np.array(embedding) for embedding in embeddings]

def get_embedding():
    """Initialize HuggingFace embeddings for ChromaDB"""
    cache_folder = os.getenv("TRANSFORMERS_CACHE", "./.embeddings_cache")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_folder=cache_folder,
        model_kwargs={'device': 'cpu'}  # Ensure CPU usage for better Docker compatibility
    )
    logger.info(f"Initialized HuggingFace embeddings with cache folder: {cache_folder}")
    
    # Wrap the embedding model to match ChromaDB's interface
    return ChromaEmbeddingWrapper(embeddings)

def _prepare_ui_schema_text(ui_schema):
    """Create rich, searchable text representation for UI schemas"""
    id_text = ui_schema.get('id', '')
    screen_id = ui_schema.get('screen_id', '')
    
    # Extract information from ui_components if available
    ui_components = ui_schema.get('ui_components', [])
    component_texts = []
    
    if isinstance(ui_components, list) and ui_components:
        for component in ui_components:
            if isinstance(component, dict):
                # Extract component type and ID
                comp_type = component.get('component_type', '')
                comp_id = component.get('id', '')
                
                # Extract text properties if available
                props = component.get('properties', {})
                text_prop = props.get('text', '')
                
                component_texts.append(f"{comp_type} {comp_id} {text_prop}")
                
                # Get text from children recursively
                children = component.get('children', [])
                if children:
                    for child in children:
                        if isinstance(child, dict):
                            child_type = child.get('component_type', '')
                            child_id = child.get('id', '')
                            child_props = child.get('properties', {})
                            child_text = child_props.get('text', '')
                            component_texts.append(f"{child_type} {child_id} {child_text}")
    
    # Join all text representations
    components_text = " ".join(component_texts)
    
    # Create a rich text representation for embedding
    if 'prospect' in id_text.lower() or 'kyc' in id_text.lower():
        text_content = f"UI SCHEMA: {id_text} {screen_id} PROSPECT INFORMATION KYC CUSTOMER DATA {components_text}"
    else:
        text_content = f"UI SCHEMA: {id_text} {screen_id} {components_text}"
    
    return text_content

def populate_vector_db():
    """Populate the vector database with action schemas, UI schemas, and API schemas"""
    collection_name = "onboarding_flow_v7"  # New collection name

    # Initialize HuggingFace embeddings
    embeddings = get_embedding()

    # Initialize ChromaDB client
    chroma_client = chromadb.HttpClient(host='3.6.132.24', port=8000)
    
    # Check if collection exists and delete it if it does
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception as e:
        print(f"Collection doesn't exist or couldn't be deleted: {e}")
    
    # Create a new collection with the HuggingFace embedding function
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embeddings
    )
    print(f"Created new collection: {collection_name}")
    
    # Get all schemas from database
    actions = get_action_schema()
    ui_schemas = get_ui_schema()
    api_schemas = get_api_schema()
    
    # Initialize lists for vector storage
    ids = []
    texts = []
    metadatas = []
    
    # Process action schemas
    print(f"Processing {len(actions)} action schemas...")
    for i, action in enumerate(actions):
        action_id = action.get('id', f"action_{i}")
        
        # Create a rich text representation for embedding
        text_content = f"ACTION: {action_id}: {action.get('desc_for_llm', 'No description')}"
        
        # Add UI ID information if available for better retrieval
        ui_id = action.get('ui_id', '')
        if ui_id:
            text_content += f" UI_ID: {ui_id}"
        
        # Add to lists for batch addition
        ids.append(f"action_{i}_{action_id}")
        texts.append(text_content)
        
        # Prepare metadata - store everything as separate fields
        metadata = {
            "type": "action",
            "action_id": action.get('id', ''),
            "stage_name": action.get('stage_name', ''),
            "desc_for_llm": action.get('desc_for_llm', ''),
            "action_type": action.get('action_type', ''),
            "next_err_action_id": action.get('next_err_action_id', ''),
            "next_success_action_id": action.get('next_success_action_id', ''),
            "ui_id": action.get('ui_id', '')
        }
        
        # Also store the full action as JSON string
        metadata["full_action"] = json.dumps(action)
        
        # Handle api_detail_id separately - if it's None, don't include it
        api_detail_id = action.get('api_detail_id')
        if api_detail_id is not None:
            metadata["api_detail_id"] = api_detail_id   
        
        metadatas.append(metadata)
    
    # Process UI schemas
    print(f"Processing {len(ui_schemas)} UI schemas...")
    ui_schema_count = 0
    for i, ui_schema in enumerate(ui_schemas):
        # Each item in ui_schemas is directly a UI schema object
        ui_schema_count += 1
        
        # Create a searchable text representation for embedding
        ui_id = ui_schema.get('id', f"ui_{i}")
        
        # Get rich text representation
        text_content = _prepare_ui_schema_text(ui_schema)
        
        # Add to lists for batch addition
        ids.append(f"ui_{i}_{ui_id}")
        texts.append(text_content)
        
        # Store metadata fields separately
        metadata = {
            "type": "ui_schema",
            "id": ui_schema.get('id', ''),
            "screen_id": ui_schema.get('screen_id', ''),
            "session_id": ui_schema.get('session_id', '')
        }
        
        # Store the full UI schema as a JSON string
        metadata["full_ui_schema"] = json.dumps(ui_schema)
        
        # Store a flag indicating if this is a prospect/KYC related schema
        prospect_related = 'prospect' in ui_id.lower() or 'kyc' in ui_id.lower()
        metadata["is_prospect_related"] = json.dumps(prospect_related) 
        
        metadatas.append(metadata)
    
    # Process API schemas
    print(f"Processing {len(api_schemas)} API schemas...")
    for i, api_schema in enumerate(api_schemas):
        api_id = api_schema.get('id', f"api_{i}")
        
        # Create a text representation for embedding
        text_content = f"API: {api_id}"
        
        # Extract API details for text enrichment
        api_details = api_schema.get('api_details', [])
        if api_details and isinstance(api_details[0], dict):
            endpoint = api_details[0].get('endpoint_path', '')
            method = api_details[0].get('http_method', '')
            text_content += f" {endpoint} {method}"
        
        # Add to lists for batch addition
        ids.append(f"api_{i}_{api_id}")
        texts.append(text_content)
        
        # Extract API details from the first item in api_details array if it exists
        api_details = api_schema.get('api_details', [])
        api_detail = api_details[0] if api_details else {}
        
        # Store metadata fields separately
        metadata = {
            "type": "api",
            "id": api_schema.get('id', ''),
            "endpoint_path": api_detail.get('endpoint_path', ''),
            "http_method": api_detail.get('http_method', '')
        }
        
        # Store request payload template and full API schema as JSON strings
        if api_detail.get('request_payload_template'):
            metadata["request_payload_template"] = json.dumps(api_detail.get('request_payload_template', {}))
        
        metadata["full_api_schema"] = json.dumps(api_schema)
        
        metadatas.append(metadata)
    
    # Add documents to vector store
    try:
        # Add documents directly to the collection in batches
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            end = min(i + batch_size, len(texts))
            collection.add(
                ids=ids[i:end],
                documents=texts[i:end],
                metadatas=metadatas[i:end]
            )
            print(f"Added batch {i//batch_size + 1} ({end-i} documents)")
        
        print(f"Successfully added {len(texts)} documents to vector store")
    except Exception as e:
        print(f"Error adding documents via ChromaDB client: {e}")
        print("Detailed error information:")
        import traceback
        traceback.print_exc()
    
    print(f"\nPopulation complete! Collection '{collection_name}' has been created with:")
    print(f"- {len(actions)} action schemas")
    print(f"- {ui_schema_count} UI schemas")
    print(f"- {len(api_schemas)} API schemas")
    
    # Test a simple query to verify the data was added correctly
    try:
        query_results = collection.query(
            query_texts=["prospect information"],
            n_results=3
        )
        print("\nVerification query for 'prospect information':")
        for i, doc in enumerate(query_results["documents"][0]):
            print(f"{i+1}. {doc[:100]}...")
    except Exception as e:
        print(f"Error during verification query: {e}")

if __name__ == "__main__":
    populate_vector_db()
