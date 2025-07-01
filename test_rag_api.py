import requests
import json
import os
import statistics
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment or use the provided one
API_KEY = os.getenv("API_KEY", "mifix-api-key-2025-secure-token")

# Define headers with API key
headers = {
    "X-API-Key": API_KEY
}

def analyze_collection_contents():
    """Analyze the contents of the ChromaDB collection to understand what data is present"""
    print("\n===== ANALYZING VECTOR DATABASE CONTENTS =====\n")
    
    # Define the API endpoint for getting all documents
    url = "http://localhost:8002/rag/query"
    
    # Use a very general query to get diverse results
    query_request = {
        "query": "Show me a diverse sample of documents",
        "n_results": 20,  # Get more results for better analysis
        "collection_name": "qna"
    }
    
    try:
        # Send the request with API key in headers
        response = requests.post(url, json=query_request, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            documents = result['results']
            
            # Collect statistics
            content_lengths = []
            sources = []
            all_tags = []
            metadata_keys = set()
            
            # Analyze each document
            for doc in documents:
                # Content length
                content_lengths.append(len(doc['content']))
                
                # Extract metadata
                meta = doc['metadata']
                for key in meta.keys():
                    metadata_keys.add(key)
                
                # Sources
                if 'source' in meta:
                    sources.append(meta['source'])
                    
                # Tags
                if 'tags' in meta and isinstance(meta['tags'], list):
                    all_tags.extend(meta['tags'])
            
            # Print collection summary
            print(f"Sample Size: {len(documents)} documents")
            print(f"\nContent Length Statistics:")
            if content_lengths:
                print(f"  - Average: {statistics.mean(content_lengths):.1f} characters")
                print(f"  - Min: {min(content_lengths)} characters")
                print(f"  - Max: {max(content_lengths)} characters")
            
            # Print metadata structure
            print(f"\nMetadata Fields: {', '.join(metadata_keys)}")
            
            # Print source distribution
            if sources:
                source_counts = Counter(sources)
                print(f"\nSource Distribution:")
                for source, count in source_counts.most_common(5):
                    print(f"  - {source}: {count} documents")
                if len(source_counts) > 5:
                    print(f"  - ... and {len(source_counts) - 5} more sources")
            
            # Print common tags
            if all_tags:
                tag_counts = Counter(all_tags)
                print(f"\nMost Common Tags:")
                for tag, count in tag_counts.most_common(10):
                    print(f"  - {tag}: {count} occurrences")
                if len(tag_counts) > 10:
                    print(f"  - ... and {len(tag_counts) - 10} more tags")
            
            # Print sample documents
            print("\n===== SAMPLE DOCUMENTS =====\n")
            for i, doc in enumerate(documents[:5]):  # Show first 5 documents
                print(f"\nDocument {i+1} (ID: {doc['id']}):")
                
                # Print content (truncated if too long)
                content = doc['content']
                if len(content) > 300:
                    content = content[:300] + "...\n[content truncated]"
                print(f"Content:\n{content}")
                
                # Print metadata
                print("\nMetadata:")
                for key, value in doc['metadata'].items():
                    if key == 'tags' and isinstance(value, list) and len(value) > 5:
                        print(f"  - {key}: {value[:5]} ... and {len(value) - 5} more tags")
                    else:
                        print(f"  - {key}: {value}")
                print("\n" + "-"*50)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {e}")

def test_rag_query():
    """Test the RAG query endpoint with a specific query"""
    print("\n===== TESTING RAG QUERY =====\n")
    print("Testing RAG query endpoint...")
    
    # Define the API endpoint
    url = "http://localhost:8002/rag/query"
    
    # Define the query request
    query_request = {
        "query": "explain the process flow in JLG and how it can be helpful?",
        "n_results": 3,
        "collection_name": "qna"
    }
    
    try:
        # Send the request with API key in headers
        response = requests.post(url, json=query_request, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            
            # Print the query
            print(f"\nQuery: {result['query']}")
            print(f"Total results: {result['total_results']}")
            
            # Print the results
            print("\nResults:")
            for i, doc in enumerate(result['results']):
                print(f"\nResult {i+1} (ID: {doc['id']}):")
                print(f"Relevance Score: {doc['relevance_score']:.4f}")
                
                # Print content (truncated if too long)
                content = doc['content']
                if len(content) > 300:
                    content = content[:300] + "...\n[content truncated]"
                print(f"Content:\n{content}")
                
                # Print metadata
                print("\nMetadata:")
                for key, value in doc['metadata'].items():
                    if key == 'tags' and isinstance(value, list) and len(value) > 5:
                        print(f"  - {key}: {value[:5]} ... and {len(value) - 5} more tags")
                    else:
                        print(f"  - {key}: {value}")
                print("\n" + "-"*50)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {e}")

def test_list_collections():
    """Test the list collections endpoint"""
    print("\n===== AVAILABLE COLLECTIONS =====\n")
    
    # Define the API endpoint
    url = "http://localhost:8002/rag/collections"
    
    try:
        # Send the request with API key in headers
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            
            # Print the collections
            collections = result['collections']
            print(f"Found {len(collections)} collections in ChromaDB:")
            for i, collection in enumerate(collections):
                print(f"  {i+1}. {collection}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test the list collections endpoint
    test_list_collections()
    
    # Analyze the collection contents
    analyze_collection_contents()
    
    # Test the RAG query endpoint with a specific query
    test_rag_query()
