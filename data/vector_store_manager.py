from typing import List
from langchain_core.documents import Document
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

class VectorStoreManager:
    """
    Manages the creation and retrieval of a vector store using FAISS.
    """
    def __init__(self, embedding_model_name: str = "nomic-embed-text"):
        """
        Initializes the VectorStoreManager with a specified Ollama embedding model.

        Args:
            embedding_model_name (str): The name of the embedding model to use.
        """
        self.embeddings = OllamaEmbeddings(model=embedding_model_name)
        print(f"VectorStoreManager initialized with model: {embedding_model_name}")

    def create_store(self, documents: List[Document]):
        """
        Creates a FAISS vector store from the provided documents.

        Args:
            documents (List[Document]): A list of documents to embed and store.

        Returns:
            FAISS: The created vector store object.
        """
        print("Creating FAISS vector store... (This may take a moment)")
        vector_store = FAISS.from_documents(documents, self.embeddings)
        print("Vector store created successfully.")
        return vector_store
