import chromadb
from sentence_transformers import SentenceTransformer
import json


def get_embedding():
    """Initialize HuggingFace embeddings for ChromaDB"""
    cache_folder = os.getenv("TRANSFORMERS_CACHE", "./.embeddings_cache")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_folder=cache_folder,
        model_kwargs={'device': 'cpu'}  # Ensure CPU usage for better Docker compatibility
    )
    logger.info(f"Initialized HuggingFace embeddings with cache folder: {cache_folder}")
    return embeddings

def get_instance():
    collection_name = "FED_WORKFLOW_V1"
    chroma_client = chromadb.HttpClient(host='3.6.132.24', port=8000)
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception as e:
        print(f"Collection doesn't exist or couldn't be deleted: {e}")
        collection = chroma_client.create_collection(name=collection_name, embedding_function=__get_embedding())
    print(f"Created new collection: {collection_name}")
    return collection

def create_embedding_document(action):
    """
    Creates a single, rich text document from an action's llm_context
    for the purpose of generating a high-quality vector embedding.
    """
    context = action.get('llm_context', {})
    
    # Combine the most important semantic fields into one text block.
    # This gives the embedding model rich context to create a distinct vector.
    document = (
        f"Stage: {action.get('stage_name', '')}\n"
        f"Purpose: {context.get('purpose', '')}\n"
        f"Key entities involved: {', '.join(context.get('entities', []))}\n"
        f"Relevant user questions: {'; '.join(context.get('example_prompts', []))}"
    )
    return document

def ingest_data(file_path='final_actions.json'):
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
    client = chromadb.PersistentClient(path="production_db")
    embedding_function = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-large-en-v1.5" # Using a top-tier model as recommended
    )
    collection = client.get_or_create_collection(
        name="unified_workflow_actions",
        embedding_function=embedding_function
    )

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
            "action_id": action['action_id'],
            "stage_name": action['stage_name']
        }
        metadata_to_store.append(metadata)

        # 3. Use the canonical action_id as the unique ID in ChromaDB
        ids_for_documents.append(action['action_id'])

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