import os
import glob
import subprocess
import time

def embed_all_docs(docs_dir, collection_name="qna"):
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
    for i, file in enumerate(doc_files):
        print(f"  {i+1}. {os.path.basename(file)}")
    
    if not doc_files:
        print("No documents found to embed.")
        return
    
    # Process each document file
    for i, file_path in enumerate(doc_files):
        file_name = os.path.basename(file_path)
        print(f"\n[{i+1}/{len(doc_files)}] Processing: {file_name}")
        
        # Call embed_single_file.py for each file
        cmd = ["python", "embed_single_file.py", file_path]
        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully processed {file_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing {file_name}: {e}")
        
        # Wait a bit between files to avoid overwhelming the server
        if i < len(doc_files) - 1:
            print("Waiting 2 seconds before processing next file...")
            time.sleep(2)
    
    print("\nAll documents processed!")

if __name__ == "__main__":
    docs_dir = os.path.join(os.getcwd(), "docs")
    embed_all_docs(docs_dir)
