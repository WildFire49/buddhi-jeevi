import json
import os
import chromadb
from chromadb.utils import embedding_functions
from database_v1 import get_action_schema, get_ui_schema, get_api_schema

# Use ChromaDB's default embedding function instead of OpenAI
embedding_function = embedding_functions.DefaultEmbeddingFunction()

def populate_vector_db():
    """Populate the vector database with action schemas"""
    collection_name = "onboarding_flow_v1"  # Use the requested collection name
    
    # Initialize ChromaDB client
    chroma_client = chromadb.HttpClient(host='3.6.132.24', port=8000)
    
    # Check if collection exists and delete it if it does
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception as e:
        print(f"Collection doesn't exist or couldn't be deleted: {e}")
    
    # Create a new collection with the default embedding function
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embedding_function
    )
    print(f"Created new collection: {collection_name}")
    
    # Helper function to ensure all metadata values are simple types
    def sanitize_metadata(metadata):
        """Convert any complex types in metadata to JSON strings"""
        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, (dict, list, tuple)):
                sanitized[key] = json.dumps(value)
            else:
                sanitized[key] = value
        return sanitized
    
    # Get all schemas from database
    actions = get_action_schema()
    ui_schemas = get_ui_schema()
    api_schemas = get_api_schema()
    
    # Initialize lists for vector storage
    ids = []
    texts = []
    metadatas = []
    
    # Process action schema
    print(f"Processing {len(actions)} action schemas...")
    for i, action in enumerate(actions):
        # Create a text representation for embedding
        action_id = action.get('action_id', f"action_{i}")
        text_content = f"ACTION: {action_id}: {action.get('desc_for_llm', 'No description')}"
        
        # Add to lists for batch addition
        ids.append(f"action_{i}_{action_id}")
        texts.append(text_content)
        
        # Prepare metadata
        metadata = {
            "type": "action",
            "action_id": action.get('action_id', ''),
            "stage_name": action.get('stage_name', ''),
            "desc_for_llm": action.get('desc_for_llm', ''),
            "action_type": action.get('action_type', ''),
            "next_action_id": action.get('next_action_id', ''),
            "next_action_text": action.get('next_action_text', ''),
            "ui_id": action.get('ui_id', ''),
            "api_detail_id": action.get('api_detail_id', ''),
            "full_action": action  # Will be converted to JSON string by sanitize_metadata
        }   
        metadatas.append(sanitize_metadata(metadata))
    
    # Process UI schema
    print(f"Processing {len(ui_schemas)} UI schemas...")
    for i, ui_schema in enumerate(ui_schemas):
        # Create a text representation for embedding
        ui_id = ui_schema.get('ui_id', f"ui_{i}")
        text_content = f"UI: {ui_id}: {ui_schema.get('desc_for_llm', 'No description')}"
        
        # Add to lists for batch addition
        ids.append(f"ui_{i}_{ui_id}")
        texts.append(text_content)
        
        # Prepare metadata
        metadata = {
            "type": "ui",
            "ui_id": ui_schema.get('ui_id', ''),
            "desc_for_llm": ui_schema.get('desc_for_llm', ''),
            "ui_type": ui_schema.get('ui_type', ''),
            "ui_components": ui_schema.get('ui_components', []),  # Will be converted to JSON string by sanitize_metadata
            "full_ui": ui_schema  # Will be converted to JSON string by sanitize_metadata
        }   
        metadatas.append(sanitize_metadata(metadata))
    
    # Process API schema
    print(f"Processing {len(api_schemas)} API schemas...")
    for i, api_schema in enumerate(api_schemas):
        # Create a text representation for embedding
        api_id = api_schema.get('api_detail_id', f"api_{i}")
        text_content = f"API: {api_id}: {api_schema.get('desc_for_llm', 'No description')}"
        
        # Add to lists for batch addition
        ids.append(f"api_{i}_{api_id}")
        texts.append(text_content)
        
        # Prepare metadata
        metadata = {
            "type": "api",
            "api_detail_id": api_schema.get('api_detail_id', ''),
            "desc_for_llm": api_schema.get('desc_for_llm', ''),
            "endpoint": api_schema.get('endpoint', ''),
            "method": api_schema.get('method', ''),
            "params": api_schema.get('params', {}),  # Will be converted to JSON string by sanitize_metadata
            "full_api": api_schema  # Will be converted to JSON string by sanitize_metadata
        }   
        metadatas.append(sanitize_metadata(metadata))
    
    # The action schema processing is already done above
    
    # Add documents to vector store using ChromaDB client directly
    try:
        # Add documents directly to the collection
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        print(f"Added {len(texts)} documents to vector store using ChromaDB client directly")
    except Exception as e:
        print(f"Error adding documents via ChromaDB client: {e}")
        print("Detailed error information:")
        import traceback
        traceback.print_exc()
    
    print(f"\nPopulation complete! Collection '{collection_name}' is ready for use.")
    print(f"Total documents added: {len(texts)}")
    
    # Test a simple query to verify the data was added correctly
    try:
        results = collection.query(
            query_texts=["JLG_S0_A1_LOGIN"],
            n_results=2
        )
        print(f"\nTest query results (searching for 'JLG_S0_A1_LOGIN'):\n")
        for i, doc in enumerate(results['documents'][0]):
            print(f"- {doc}")
            metadata = results['metadatas'][0][i]
            print(f"  Action ID: {metadata.get('action_id', 'N/A')}")
    except Exception as e:
        print(f"Error testing query: {e}")

if __name__ == "__main__":
    populate_vector_db()
