import os
import json
import glob
import traceback
from typing import List, Dict, Any
import chromadb
import docx2txt
import PyPDF2
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

def load_document(file_path: str) -> List[str]:
    """
    Load a document from file path based on its extension.
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        List[str]: List of document chunks
    """
    print(f"Loading {file_path}...")
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            # Use PyPDF2 to extract text from PDF
            text_content = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
            return text_content
            
        elif file_ext == '.docx':
            # Use docx2txt to extract text from DOCX
            text = docx2txt.process(file_path)
            # Split by double newlines to get paragraphs
            paragraphs = text.split('\n\n')
            return [p for p in paragraphs if p.strip()]  # Filter out empty paragraphs
            
        elif file_ext == '.json':
            # For JSON files, we'll extract all text values
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract text from JSON (flattening the structure)
            def extract_text_from_json(obj, texts=None):
                if texts is None:
                    texts = []
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, str) and value.strip():
                            texts.append(value)
                        else:
                            extract_text_from_json(value, texts)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_text_from_json(item, texts)
                
                return texts
            
            return extract_text_from_json(data)
        
        else:
            print(f"Unsupported file type: {file_ext}")
            return []
            
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return []

def split_text(texts: List[str], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks for embedding.
    
    Args:
        texts (List[str]): List of text documents
        chunk_size (int): Size of each chunk
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    
    chunks = []
    for text in texts:
        if text.strip():  # Skip empty texts
            doc_chunks = text_splitter.split_text(text)
            chunks.extend(doc_chunks)
    
    return chunks

def embed_docs_to_chroma(docs_dir: str, collection_name: str = "qna"):
    """
    Embed all documents from a directory into ChromaDB.
    
    Args:
        docs_dir (str): Path to the directory containing documents
        collection_name (str): Name of the ChromaDB collection
    """
    # Check if directory exists
    if not os.path.exists(docs_dir):
        print(f"Directory does not exist: {docs_dir}")
        return
    
    # Get all document files
    supported_extensions = ['.pdf', '.docx', '.json']
    doc_files = []
    
    for ext in supported_extensions:
        doc_files.extend(glob.glob(os.path.join(docs_dir, f"*{ext}")))
    
    print(f"Found {len(doc_files)} document files in {docs_dir}")
    for file in doc_files:
        print(f"  - {os.path.basename(file)}")
    
    if not doc_files:
        print("No documents found to embed.")
        return
    
    try:
        print("\nInitializing ChromaDB client...")
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host='3.6.132.24', port=8000)
        
        print("Initializing HuggingFace embeddings...")
        # Initialize HuggingFace embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Get or create collection
        try:
            print(f"Connecting to collection: {collection_name}")
            collection = client.get_collection(name=collection_name)
            print(f"Connected to existing collection: {collection_name}")
        except Exception as e:
            print(f"Collection {collection_name} not found, creating new collection: {str(e)}")
            collection = client.create_collection(name=collection_name)
        
        # Process each document file
        for file_path in doc_files:
            file_name = os.path.basename(file_path)
            print(f"\nProcessing file: {file_name}")
            
            try:
                # Load document
                doc_texts = load_document(file_path)
                
                if not doc_texts:
                    print(f"No content extracted from {file_name}, skipping...")
                    continue
                
                print(f"Extracted {len(doc_texts)} text segments from {file_name}")
                
                # Split into chunks
                chunks = split_text(doc_texts)
                print(f"Created {len(chunks)} chunks from {file_name}")
                
                if not chunks:
                    print(f"No chunks created from {file_name}, skipping...")
                    continue
                
                # Process in smaller batches
                batch_size = 5  # Process 5 chunks at a time
                for batch_idx in range(0, len(chunks), batch_size):
                    end_idx = min(batch_idx + batch_size, len(chunks))
                    current_batch = chunks[batch_idx:end_idx]
                    batch_num = batch_idx // batch_size + 1
                    total_batches = (len(chunks) + batch_size - 1) // batch_size
                    
                    print(f"Processing batch {batch_num}/{total_batches} for {file_name}")
                    
                    # Generate IDs for this batch
                    batch_ids = [f"doc_{file_name}_{batch_idx + i}" for i in range(len(current_batch))]
                    
                    # Generate embeddings for this batch
                    print(f"  Generating embeddings for {len(current_batch)} chunks...")
                    batch_embeddings = []
                    for chunk in current_batch:
                        try:
                            embedding = embeddings.embed_query(chunk)
                            batch_embeddings.append(embedding)
                        except Exception as e:
                            print(f"Error generating embedding: {e}")
                            traceback.print_exc()
                            # Use a zero vector as fallback
                            batch_embeddings.append([0.0] * 384)  # Default dimension for all-MiniLM-L6-v2
                    
                    # Prepare metadata for this batch
                    batch_metadatas = [{
                        "source": file_name,
                        "chunk_id": batch_idx + i,
                        "file_type": os.path.splitext(file_name)[1][1:],  # Remove the dot from extension
                    } for i in range(len(current_batch))]
                    
                    # Add documents to collection
                    try:
                        print(f"  Adding {len(current_batch)} chunks to collection...")
                        collection.add(
                            ids=batch_ids,
                            embeddings=batch_embeddings,
                            documents=current_batch,
                            metadatas=batch_metadatas
                        )
                        print(f"  Successfully added batch {batch_num}/{total_batches}")
                    except Exception as e:
                        print(f"Error adding documents to collection: {e}")
                        traceback.print_exc()
                
                print(f"Successfully processed {file_name}")
                
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                traceback.print_exc()
        
        # Get total count of documents in collection
        try:
            print("\nGetting collection statistics...")
            collection_data = collection.get()
            total_docs = len(collection_data['ids']) if 'ids' in collection_data else 0
            print(f"Total documents in collection {collection_name}: {total_docs}")
        except Exception as e:
            print(f"Error getting collection statistics: {e}")
            traceback.print_exc()
        
    except Exception as e:
        print(f"Error embedding documents: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    docs_dir = os.path.join(os.getcwd(), "docs")
    embed_docs_to_chroma(docs_dir)
