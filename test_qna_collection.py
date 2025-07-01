import os
import chromadb
import warnings
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Disable ChromaDB telemetry
os.environ["CHROMADB_TELEMETRY"] = "0"

# Load environment variables
load_dotenv()

# Suppress warnings
warnings.filterwarnings("ignore")

def test_qna_collection():
    """Test the 'qna' collection in ChromaDB"""
    try:
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host='3.6.132.24', port=8000)
        
        # Get the collection
        try:
            collection = client.get_collection("qna")
            print(f"Successfully connected to 'qna' collection")
            
            # Get collection info
            count = collection.count()
            print(f"Collection contains {count} documents")
            
            # Test a query
            test_query = "What is the market landscape for Fin Tech in Tamil Nadu?"
            results = collection.query(
                query_texts=[test_query],
                n_results=3
            )
            
            # Display results
            if results and results['documents'] and results['documents'][0]:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0]
                ids = results['ids'][0]
                
                print(f"\nFound {len(docs)} relevant documents for test query:")
                for i, (doc, meta, doc_id) in enumerate(zip(docs, metadatas, ids)):
                    print(f"\nResult {i+1} (ID: {doc_id}):")
                    print(f"Content: {doc[:150]}...")
                    print(f"Source: {meta.get('source', 'Unknown')}")
                    print(f"Tags: {meta.get('tags', 'None')}")
            else:
                print("No results found for the test query.")
                
        except Exception as e:
            print(f"Error: Collection 'qna' not found. {e}")
            print("The collection may not have been created successfully.")
            
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")

if __name__ == "__main__":
    test_qna_collection()
