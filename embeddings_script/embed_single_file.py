import os
import sys
import chromadb
import PyPDF2
import docx2txt
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

def embed_file_to_chroma(file_path, collection_name="qna"):
    """
    Embed a single file into ChromaDB.
    
    Args:
        file_path (str): Path to the file to embed
        collection_name (str): Name of the ChromaDB collection
    """
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return
    
    file_name = os.path.basename(file_path)
    print(f"Processing file: {file_name}")
    
    # Read file content based on file type
    file_ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    try:
        if file_ext == '.pdf':
            # Handle PDF files
            print("Detected PDF file, using PyPDF2 to extract text...")
            text_parts = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = "\n\n".join(text_parts)
            print(f"Extracted {len(text)} characters from PDF with {len(text_parts)} pages")
            
        elif file_ext == '.docx':
            # Handle DOCX files
            print("Detected DOCX file, using docx2txt to extract text...")
            text = docx2txt.process(file_path)
            print(f"Extracted {len(text)} characters from DOCX")
            
        elif file_ext == '.json':
            # Handle JSON files
            print("Detected JSON file, reading as text...")
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"Read {len(text)} characters from JSON")
            
        else:
            # Handle text files
            print("Treating as text file...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                print(f"Successfully read file: {len(text)} characters")
            except UnicodeDecodeError:
                # Try with a different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
                print(f"Successfully read file with latin-1 encoding: {len(text)} characters")
        
        if not text.strip():
            print("Warning: Extracted text is empty!")
            return
            
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    print(f"Split text into {len(chunks)} chunks")
    
    try:
        # Initialize ChromaDB client
        print("Connecting to ChromaDB...")
        client = chromadb.HttpClient(host='3.6.132.24', port=8000)
        
        # Initialize HuggingFace embeddings
        print("Initializing embeddings model...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Get or create collection
        try:
            collection = client.get_collection(name=collection_name)
            print(f"Connected to existing collection: {collection_name}")
        except Exception as e:
            print(f"Creating new collection: {collection_name}")
            collection = client.create_collection(name=collection_name)
        
        # Generate IDs for chunks
        doc_ids = [f"doc_{file_name}_{i}" for i in range(len(chunks))]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(chunks)} chunks...")
        doc_embeddings = []
        for i, chunk in enumerate(chunks):
            if i > 0 and i % 5 == 0:
                print(f"  Generated {i}/{len(chunks)} embeddings")
            embedding = embeddings.embed_query(chunk)
            doc_embeddings.append(embedding)
        
        # Prepare metadata
        metadatas = [{
            "source": file_name,
            "chunk_id": i,
            "file_type": os.path.splitext(file_name)[1][1:] if os.path.splitext(file_name)[1] else "txt"
        } for i in range(len(chunks))]
        
        # Add to collection in small batches
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            end_idx = min(i + batch_size, len(chunks))
            batch_num = i // batch_size + 1
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            print(f"Adding batch {batch_num}/{total_batches} to collection...")
            collection.add(
                ids=doc_ids[i:end_idx],
                embeddings=doc_embeddings[i:end_idx],
                documents=chunks[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
        
        print(f"Successfully embedded {file_name} into {collection_name}")
        
        # Get collection count
        collection_data = collection.get()
        total_docs = len(collection_data['ids']) if 'ids' in collection_data else 0
        print(f"Total documents in collection {collection_name}: {total_docs}")
        
    except Exception as e:
        print(f"Error embedding file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python embed_single_file.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    embed_file_to_chroma(file_path)
