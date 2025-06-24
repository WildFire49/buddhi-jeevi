import os
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import ElasticsearchStore
from langchain_core.documents import Document
from database import get_mock_vector_db
from elasticsearch import Elasticsearch

# Load environment variables
load_dotenv()

def populate_vector_db():
    """Populate the Elasticsearch vector database with actions from database.py"""
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="nomic-embed-text"
    )
    
    # Initialize Elasticsearch client to delete existing index
    es_client = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])
    index_name = "loan_actions_index_v5"  # Changed version to avoid conflicts
    
    # Delete existing index if it exists
    if es_client.indices.exists(index=index_name):
        es_client.indices.delete(index=index_name)
        print(f"Deleted existing index: {index_name}")
    
    # Initialize vector store with new index
    vector_store = ElasticsearchStore(
        es_url="http://localhost:9200/",
        index_name=index_name,
        embedding=embeddings
    )
    
    # Get all actions from database
    actions = get_mock_vector_db()
    
    # Convert actions to documents for vector storage
    documents = []
    for action in actions:
        # Create a text representation for embedding
        text_content = f"""
        # Action ID: {action['action_id']}
        # Stage: {action['stage_name']}
        Description: {action['description_for_llm']}
        # Action Type: {action['action_type']}
        """
        
        # Create document with metadata containing the full action
        doc = Document(
            page_content=text_content,
            metadata={
                "action_id": action['action_id'],
                # "stage_name": action['stage_name'],
                "action_type": action['action_type'],
                "ui_tags": action['ui_tags'],
                "next_action_id": action['next_action_id'],
                "full_action": json.dumps(action)  # Store the complete action as JSON string in metadata
            }
        )
        documents.append(doc)
    
    # Add documents to vector store
    try:
        vector_store.add_documents(documents)
        print(f"Successfully added {len(documents)} actions to vector database")
        
        # Test retrieval
        test_query = "I want to login to the system"
        results = vector_store.similarity_search(test_query, k=1)
        if results:
            print(f"Test query successful. Retrieved: {results[0].metadata['action_id']}")
        else:
            print("Test query failed - no results found")
            
    except Exception as e:
        print(f"Error populating vector database: {e}")

if __name__ == "__main__":
    populate_vector_db()
