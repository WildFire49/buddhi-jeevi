import json
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import chromadb
from database_v1 import get_action_schema, get_ui_schema, get_api_schema

# Load environment variables
load_dotenv()
print(os.getenv("OPENAI_API_KEY"))
# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-3-small"
)

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
    
    # Create a new collection
    chroma_client.create_collection(name=collection_name)
    print(f"Created new collection: {collection_name}")
    
    # Initialize vector store with the collection
    vector_store = Chroma(
        client=chroma_client,
        collection_name=collection_name,
        embedding_function=embeddings
    )
    
    # Get all schemas from database
    actions = get_action_schema()
    ui_schemas = get_ui_schema()
    api_schemas = get_api_schema()
    
    # Convert actions to documents for vector storage
    documents = []
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
            "full_action": json.dumps(action)  # Store the complete action as JSON string
        }   
        metadatas.append(metadata)
        
        # Also create a Document object for LangChain's add_documents method
        doc = Document(
            page_content=text_content,
            metadata=metadata
        )
        documents.append(doc)
    
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
            "ui_components": ui_schema.get('ui_components', []),
            "full_ui": json.dumps(ui_schema)  # Store the complete UI schema as JSON string
        }   
        metadatas.append(metadata)
        
        # Also create a Document object for LangChain's add_documents method
        doc = Document(
            page_content=text_content,
            metadata=metadata
        )
        documents.append(doc)
    
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
            "params": json.dumps(api_schema.get('params', {})),
            "full_api": json.dumps(api_schema)  # Store the complete API schema as JSON string
        }   
        metadatas.append(metadata)
        
        # Also create a Document object for LangChain's add_documents method
        doc = Document(
            page_content=text_content,
            metadata=metadata
        )
        documents.append(doc)
    
    # The action schema processing is already done above
    
    # Add documents to vector store
    try:
        # First try using the LangChain Chroma add_documents method
        vector_store.add_documents(documents)
        print(f"Added {len(documents)} documents to vector store using LangChain")
    except Exception as e:
        print(f"Error adding documents via LangChain: {e}")
        try:
            # Fallback to using the ChromaDB client directly
            collection = chroma_client.get_collection(name=collection_name)
            collection.add(
                ids=ids,
                embeddings=None,  # Let ChromaDB generate embeddings
                documents=texts,
                metadatas=metadatas
            )
            print(f"Added {len(texts)} documents to vector store using ChromaDB client directly")
        except Exception as e2:
            print(f"Error adding documents via ChromaDB client: {e2}")
    
    print(f"\nPopulation complete! Collection '{collection_name}' is ready for use.")
    print(f"Total documents added: {len(documents)}")
    
    # Test a simple query to verify the data was added correctly
    try:
        results = vector_store.similarity_search("JLG_S0_A1_LOGIN", k=2)
        print(f"\nTest query results (searching for 'validate OTP'):\n")
        for doc in results:
            print(f"- {doc.page_content}")
            print(f"  Action ID: {doc.metadata.get('action_id', 'N/A')}")
    except Exception as e:
        print(f"Error testing query: {e}")

if __name__ == "__main__":
    populate_vector_db()
