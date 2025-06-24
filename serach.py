from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import OllamaEmbeddings

# --- PREREQUISITES ---
# 1. Your Elasticsearch instance is running at http://localhost:9200
# 2. Your Ollama server is running

ES_URL = "http://localhost:9200"
INDEX_NAME = "loan_actions_index_v5" # The name of the index you created

# --- SETUP ---
# Initialize the same embedding model used for indexing
embedding_model = OllamaEmbeddings(model="text-embedding-3-small")

# Connect to your existing Elasticsearch index
# This object knows how to talk to your vector DB
vector_store = ElasticsearchStore(
    es_url=ES_URL,
    index_name=INDEX_NAME,
    embedding=embedding_model
    # If using security, add: es_user="elastic", es_password="YOUR_PASSWORD"
)

# --- THE SEARCH ---
query = "What information do I need to sign in to the system?"

# `similarity_search` automatically does two things:
# 1. Converts your `query` string into a vector using the embedding_model.
# 2. Sends that vector to Elasticsearch to perform a kNN search.
# `k` specifies how many results you want back.
try:
    print(f"Searching for documents similar to: '{query}'")
    
    # Perform the similarity search
    results = vector_store.similarity_search(query, k=2)

    # Print the results
    print("\n--- Search Results ---")
    for doc in results:
        print(f"Page Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}\n")
        
except Exception as e:
    print(f"An error occurred during search: {e}")