import os
import json
import glob
from typing import List
import chromadb
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

def load_json_files(directory_path: str) -> List[dict]:
    """
    Load all JSON files from the specified directory.
    
    Args:
        directory_path (str): Path to the directory containing JSON files.
        
    Returns:
        List[dict]: List of JSON objects loaded from files.
    """
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    data_objects = []
    
    print(f"Found {len(json_files)} JSON files in {directory_path}")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source_file'] = os.path.basename(file_path)
                data_objects.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    print(f"Successfully loaded {len(data_objects)} JSON objects")
    return data_objects



def create_qna_collection(data_objects: List[dict]):
    """
    Create a ChromaDB collection with the provided data objects.
    
    Args:
        data_objects (List[dict]): List of JSON objects to embed.
    """
    try:
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host='3.6.132.24', port=8000)
        
        # Initialize HuggingFace embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Check if collection exists, if not create it
        try:
            collection = client.get_collection("qna")
            print("Collection 'qna' already exists")
        except Exception:
            collection = client.create_collection(
                name="qna",
                metadata={"hnsw:space": "cosine"}
            )
            print("Created new collection 'qna'")
        
        # Prepare documents, metadatas, and ids
        documents = []
        metadatas = []
        ids = []
        
        # Process each data object
        for i, obj in enumerate(data_objects):
            # Extract text content
            text_content = obj.get('text', '')
            
            # Extract tags and join them
            tags = obj.get('tag', [])
            tag_text = ", ".join(tags) if tags else ""
            
            # Create document
            documents.append(text_content)
            
            # Create metadata
            metadatas.append({
                'source': obj.get('metadata', ''),
                'source_file': obj.get('source_file', ''),
                'tags': tag_text
            })
            
            # Create ID
            ids.append(f"smart_chunk_{i}")
        
        # Generate embeddings for each document
        embeddings_list = []
        for doc in documents:
            embedding = embeddings.embed_query(doc)
            embeddings_list.append(embedding)
        
        # Add documents to collection
        collection.add(
            embeddings=embeddings_list,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Successfully added {len(documents)} documents to ChromaDB collection 'qna'")
        
        return collection
    
    except Exception as e:
        print(f"Error creating ChromaDB collection: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    try:
        # Path to smart_chunks directory
        smart_chunks_dir = os.path.join(os.getcwd(), "smart_chunks")
        print(f"Looking for smart_chunks directory at: {smart_chunks_dir}")
        
        if not os.path.exists(smart_chunks_dir):
            print(f"ERROR: Directory not found: {smart_chunks_dir}")
            return
        
        # Load JSON files
        data_objects = load_json_files(smart_chunks_dir)
        
        if not data_objects:
            print("ERROR: No data objects were loaded. Cannot proceed.")
            return
        
        # Create ChromaDB collection and add documents
        print("Attempting to create/access ChromaDB collection 'qna'...")
        collection = create_qna_collection(data_objects)
        
        if not collection:
            print("ERROR: Failed to create or access ChromaDB collection.")
            return
        
        # Test retrieval
        try:
            print("\nTesting retrieval from the new collection...")
            test_query = "What is the market landscape for Fin Tech in Tamil Nadu?"
            
            # Query the collection
            results = collection.query(
                query_texts=[test_query],
                n_results=3
            )
            
            # Display results
            if results and results['documents'] and results['documents'][0]:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0] if 'distances' in results else [None] * len(docs)
                
                print(f"Found {len(docs)} relevant documents for test query:")
                for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances)):
                    print(f"\nResult {i+1}:")
                    print(f"Content: {doc[:100]}...")
                    print(f"Source: {meta.get('source', 'Unknown')}")
                    print(f"Tags: {meta.get('tags', 'None')}")
                    if dist is not None:
                        print(f"Relevance: {1 - dist:.4f}")
            else:
                print("No results found for the test query.")
        except Exception as e:
            print(f"Error during test retrieval: {e}")
    
    except Exception as e:
        print(f"ERROR in main function: {e}")

if __name__ == "__main__":
    main()
