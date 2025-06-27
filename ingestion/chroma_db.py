import chromadb
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import json
import uuid
import numpy as np


class ChromaEmbeddingFunction:
    """Wrapper for LangChain embeddings to match ChromaDB's expected interface"""
    
    def __init__(self):
        cache_folder = os.getenv("TRANSFORMERS_CACHE", "./.embeddings_cache")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=cache_folder,
            model_kwargs={'device': 'cpu'}  # Ensure CPU usage for better Docker compatibility
        )
        print(f"Initialized HuggingFace embeddings with cache folder: {cache_folder}")
    
    def __call__(self, input):
        """ChromaDB expects a function with signature (self, input) -> List[List[float]]
        The return value must be a NumPy array or have a .tolist() method"""
        embeddings = self.embeddings.embed_documents(input)
        # Convert to numpy array to ensure it has tolist() method
        return np.array(embeddings)

def get_embedding():
    """Initialize embedding function for ChromaDB"""
    return ChromaEmbeddingFunction()

def get_instance():
    collection_name = "FED_WORKFLOW_V1"
    chroma_client = chromadb.HttpClient(host='3.6.132.24', port=8000)
    
    # Try to delete the collection if it exists
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception as e:
        print(f"Collection doesn't exist or couldn't be deleted: {e}")
    
    # Create a new collection with our embedding function
    try:
        embedding_function = get_embedding()
        collection = chroma_client.create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        print(f"Created new collection: {collection_name}")
        return collection
    except Exception as e:
        print(f"Error creating collection: {e}")
        raise

def create_embedding_document(action):
    """
    Creates a single, rich text document from an action's llm_context
    for the purpose of generating a high-quality vector embedding.
    """
    context = action.get('llm_context', {})
    
    # Combine the most important semantic fields into one text block.
    # This gives the embedding model rich context to create a distinct vector.
    document = (
        f"Stage: {action.get('action_id', '')}\n"
        f"Purpose: {context.get('purpose', '')}\n"
        f"Key entities involved: {', '.join(context.get('entities', []))}\n"
        f"Relevant user questions: {'; '.join(context.get('example_prompts', []))}"
    )
    return document

def ingest_data(file_path='./workflow/workflow_v1.json'):
    """
    Loads unified action documents from a file and ingests them into ChromaDB
    using the optimal 'Embed the Meaning, Store the Blueprint' strategy.
    """
    try:
        with open(file_path, 'r') as f:
            all_actions = json.load(f)
        print(f"Loaded {len(all_actions)} unified action documents from '{file_path}'.")
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # Initialize ChromaDB and the embedding model
    # client = chromadb.PersistentClient(path="production_db")
    # embedding_function = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
    #     model_name="BAAI/bge-large-en-v1.5" # Using a top-tier model as recommended
    # )
    # collection = client.get_or_create_collection(
    #     name="unified_workflow_actions",
    #     embedding_function=embedding_function
    # )
    collection = get_instance()


    # Prepare lists for batch ingestion
    documents_for_embedding = []
    metadata_to_store = []
    ids_for_documents = []

    for action in all_actions:
        # 1. Create the rich text document for the vector
        doc_text = create_embedding_document(action)
        documents_for_embedding.append(doc_text)
        
        # 2. Prepare the metadata. We store the entire object as a JSON string.
        # This is the 'blueprint' we get back after the search.
        metadata = {
            # Storing the entire object ensures we get everything back.
            # ChromaDB metadata values must be strings, ints, floats, or bools.
            "full_action_json": json.dumps(action),
            
            # Also store key fields at the top level for potential filtering.
            "action_id": action.get('action_id', ''),
            "stage_name": action.get('stage_name', ''),
            "ui_components": json.dumps(action.get('ui_definition', {}).get('ui_components', [])),
            "next_action_id": action.get('workflow_logic', {}).get('next_action_id', ''),
            "next_success_action_id": action.get('workflow_logic', {}).get('next_success_action_id', ''),
            "next_err_action_id": action.get('workflow_logic', {}).get('error_action_id', ''),
            "title": action.get('title', '')
        }
        metadata_to_store.append(metadata)

        # 3. Use the canonical action_id as the unique ID in ChromaDB, or generate UUID if missing
        action_id = action.get('action_id')
        if action_id:
            ids_for_documents.append(action_id)
        else:
            # Generate a unique ID if action_id is missing
            ids_for_documents.append(str(uuid.uuid4()))

    # Ingest the data in a single batch for efficiency
    print(f"Ingesting {len(ids_for_documents)} documents into ChromaDB...")
    collection.add(
        ids=ids_for_documents,
        documents=documents_for_embedding,
        metadatas=metadata_to_store
    )
    print("✅ Ingestion complete.")
    print(f"Total items in collection: {collection.count()}")

if __name__ == "__main__":
    # You would first need to create the 'final_actions.json' file
    # containing all your unified action objects.
    # For now, let's assume it exists and run the ingestion.
    ingest_data()