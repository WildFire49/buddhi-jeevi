import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define request and response models
class RagQueryRequest(BaseModel):
    """Request model for RAG query endpoint"""
    query: str = Field(..., description="The query text to search for in the vector database")
    n_results: int = Field(3, description="Number of results to return")
    collection_name: str = Field("qna", description="Name of the ChromaDB collection to query")

class RagDocument(BaseModel):
    """Document model for RAG response"""
    id: str
    content: str
    metadata: Dict[str, Any]
    relevance_score: float

class RagQueryResponse(BaseModel):
    """Response model for RAG query endpoint"""
    query: str
    results: List[RagDocument]
    total_results: int

async def query_rag_collection(request: RagQueryRequest) -> RagQueryResponse:
    """
    Query the ChromaDB collection with the given query text.
    
    Args:
        request: RagQueryRequest containing query text and parameters
        
    Returns:
        RagQueryResponse with query results
    """
    try:
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host='3.6.132.24', port=8000)
        
        # Get the collection
        try:
            collection = client.get_collection(request.collection_name)
        except Exception as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Collection '{request.collection_name}' not found: {str(e)}"
            )
        
        # Initialize HuggingFace embeddings for query
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Generate embedding for the query
        query_embedding = embeddings.embed_query(request.query)
        
        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.n_results
        )
        
        # Process results
        documents = []
        if results and results['documents'] and results['documents'][0]:
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            ids = results['ids'][0]
            distances = results['distances'][0] if 'distances' in results else [None] * len(docs)
            
            for i, (doc, meta, doc_id, dist) in enumerate(zip(docs, metadatas, ids, distances)):
                # Convert distance to relevance score (1 - distance for cosine distance)
                relevance = 1.0 - dist if dist is not None else 0.0
                
                # Create document object
                document = RagDocument(
                    id=doc_id,
                    content=doc,
                    metadata=meta,
                    relevance_score=relevance
                )
                documents.append(document)
        
        # Create response
        response = RagQueryResponse(
            query=request.query,
            results=documents,
            total_results=len(documents)
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying RAG collection: {str(e)}")

def register_rag_endpoints(app: FastAPI):
    """
    Register RAG endpoints with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    @app.post("/rag/query", response_model=RagQueryResponse)
    async def rag_query(request: Request, query_request: RagQueryRequest):
        """
        Query the RAG system with the given query text.
        
        Args:
            request: FastAPI request object
            query_request: RagQueryRequest containing query parameters
            
        Returns:
            RagQueryResponse with query results
        """
        return await query_rag_collection(query_request)
    
    @app.get("/rag/collections")
    async def list_collections(request: Request):
        """
        List available collections in the ChromaDB instance.
        
        Args:
            request: FastAPI request object
            
        Returns:
            List of collection names
        """
        try:
            # Initialize ChromaDB client
            client = chromadb.HttpClient(host='3.6.132.24', port=8000)
            
            # Get all collections
            collections = client.list_collections()
            collection_names = [collection.name for collection in collections]
            
            return {"collections": collection_names}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")
