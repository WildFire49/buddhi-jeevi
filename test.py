import chromadb

client = chromadb.HttpClient(host="3.6.132.24", port=8000)

# List all collections
collections = client.list_collections()

for c in collections:
    print(f"\n🔍 Collection: {c.name}")
    collection = client.get_collection(name=c.name)
    
    # Fetch all documents (limit results if large)
    results = collection.get()
    
    # Print document IDs and metadata
    for idx, doc_id in enumerate(results["ids"]):
        print(f"  ➤ Document ID: {doc_id}")
        if "metadatas" in results and results["metadatas"]:
            print(f"     Metadata: {results['metadatas'][idx]}")
        if "documents" in results and results["documents"]:
            print(f"     Document: {results['documents'][idx][:100]}...")  # first 100 chars
