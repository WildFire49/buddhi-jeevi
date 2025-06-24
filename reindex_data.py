from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import OllamaEmbeddings
import os
from langchain_core.documents import Document
import json

# Import the mock database function
from database import get_mock_vector_db

# --- Configuration ---
ES_URL = "http://localhost:9200/"
INDEX_NAME = "loan_actions_index_v2"
EMBEDDING_MODEL_NAME = "nomic-embed-text"

# --- Load data from database.py ---
print("Loading data from database.py...")
raw_action_documents = get_mock_vector_db()
documents = []

for doc_data in raw_action_documents:
    # Combine relevant fields into a single string for page_content
    content = f"Action ID: {doc_data.get('action_id', 'N/A')}\n" \
              f"Stage: {doc_data.get('stage_name', 'N/A')}\n" \
              f"Description: {doc_data.get('description_for_llm', 'N/A')}\n" \
              f"Action Type: {doc_data.get('action_type', 'N/A')}\n" \
              f"API Endpoint Ref: {doc_data.get('api_endpoint_ref', 'N/A')}"

    if doc_data.get('ui_definition'):
        content += f"\nUI Step Title: {doc_data['ui_definition'].get('step_title', 'N/A')}\n" \
                   f"UI Bot Message: {doc_data['ui_definition'].get('bot_message', 'N/A')}"

    if doc_data.get('api_call_details'):
        content += f"\nAPI Method: {doc_data['api_call_details'].get('http_method', 'N/A')}\n" \
                   f"API Path: {doc_data['api_call_details'].get('endpoint_path', 'N/A')}"

    # Store original data or key identifiers in metadata for retrieval/filtering
    metadata = {k: v for k, v in doc_data.items() if k not in ['ui_definition', 'api_call_details']}
    print("content :", content)
    print("metadata :",metadata)
    documents.append(Document(page_content=content, metadata=metadata))

print(f"Prepared {len(documents)} documents for indexing.")

# --- Initialize embedding model ---
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

# --- Create or update Elasticsearch index ---
print(f"Re-indexing data into Elasticsearch index '{INDEX_NAME}' with embeddings from '{EMBEDDING_MODEL_NAME}'...")

es_store = ElasticsearchStore.from_documents(
    documents, embeddings, es_url=ES_URL, index_name=INDEX_NAME, # Ensure index_name is passed
    # The metadatas argument is automatically handled by from_documents when Document objects are passed
)

print("Re-indexing complete.")