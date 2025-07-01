import os
import json
import glob
import chromadb
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

def embed_text_to_chroma(text_chunks, source_name, collection_name="qna"):
    """
    Embed text chunks into ChromaDB.
    
    Args:
        text_chunks (list): List of text chunks to embed
        source_name (str): Name of the source document
        collection_name (str): Name of the ChromaDB collection
    """
    try:
        print(f"Embedding {len(text_chunks)} chunks from {source_name}...")
        
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host='3.6.132.24', port=8000)
        
        # Initialize HuggingFace embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Get or create collection
        try:
            collection = client.get_collection(name=collection_name)
            print(f"Connected to existing collection: {collection_name}")
        except Exception as e:
            print(f"Collection {collection_name} not found, creating new collection")
            collection = client.create_collection(name=collection_name)
        
        # Generate IDs for chunks
        doc_ids = [f"doc_{source_name}_{i}" for i in range(len(text_chunks))]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(text_chunks)} chunks...")
        doc_embeddings = []
        for chunk in text_chunks:
            embedding = embeddings.embed_query(chunk)
            doc_embeddings.append(embedding)
        
        # Prepare metadata
        metadatas = [{
            "source": source_name,
            "chunk_id": i,
        } for i in range(len(text_chunks))]
        
        # Add to collection
        print(f"Adding {len(text_chunks)} chunks to collection...")
        collection.add(
            ids=doc_ids,
            embeddings=doc_embeddings,
            documents=text_chunks,
            metadatas=metadatas
        )
        
        print(f"Successfully embedded {len(text_chunks)} chunks from {source_name}")
        
    except Exception as e:
        print(f"Error embedding text: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to embed text from a file"""
    # Get file path from user
    print("Enter the path to the text file to embed:")
    file_path = input().strip()
    
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    # Get source name from file path
    source_name = os.path.basename(file_path)
    
    # Embed chunks
    embed_text_to_chroma(chunks, source_name)

if __name__ == "__main__":
    main()
