import os
import json
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import ElasticsearchStore
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from llm_client import LLMManager 
import chromadb

# Load environment variables
load_dotenv()

class RAGChainBuilder:
    """
    A Singleton class to build and provide a single instance of the RAG chain.
    This prevents re-initializing models and retrievers unnecessarily.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        The __new__ method is called before __init__ and is used to control
        the object creation process. This is the standard way to implement a Singleton.
        """
        if not cls._instance:
            print("Creating a new RAGChainBuilder instance...")
            # Create a new instance of the class
            cls._instance = super(RAGChainBuilder, cls).__new__(cls)
        else:
            print("Returning existing RAGChainBuilder instance...")
        return cls._instance

    def __init__(self, llm_model_name: str = "gpt-3.5-turbo"):
        """
        Initializes the RAGChainBuilder's attributes.
        This will only run the first time the instance is created.

        Args:
            vector_store (FAISS): The vector store to retrieve context from.
            llm_model_name (str): The name of the OpenAI chat model to use for generation.
        """
        # The hasattr check prevents re-initialization on subsequent calls to get the instance
        if not hasattr(self, 'is_initialized'):

            # Initialize ChromaDB client
            client = chromadb.HttpClient(host='3.6.132.24', port=8000)
            
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model="text-embedding-3-small"
            )
            
            # Initialize Chroma vector store with onboarding_flow collection
            self.vector_store = Chroma(
                client=client,
                collection_name="onboarding_flow",    # Use the onboarding_flow collection
                embedding_function=self.embeddings
            )
            self.llm = LLMManager(model_name=llm_model_name).llm
            self.is_initialized = True
            print(f"RAGChainBuilder initialized with model: {llm_model_name}")
            self.rag_chain = self._build_chain()

    def _format_context(self, docs):
        """Format retrieved documents for the prompt"""
        if not docs:
            return "No relevant actions found."
        
        # Get the most relevant document
        doc = docs[0]
        if 'full_action' in doc.metadata:
            return doc.metadata['full_action']
        return doc.page_content

    def _build_chain(self):
        """
        A private method to construct the RAG chain.
        """
        prompt = ChatPromptTemplate.from_template("""
        You are an expert assistant for a financial services application. 
        Based on the user's question, you need to return the most relevant action from the context.
        
        If the context contains a relevant action (in JSON format), return ONLY that JSON action as-is.
        If no relevant action is found, respond with a helpful message.

        CONTEXT:
        {context}

        QUESTION:
        {question}

        RESPONSE:
        """)
        
        chain = (
            {
                "context": self.vector_store.as_retriever() | self._format_context, 
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("RAG chain built successfully.")
        return chain
    
    def get_chain(self):
        """
        Public method to get the constructed RAG chain.
        """
        return self.rag_chain

    def get_action_directly(self, question: str):
        """
        Get action directly from vector store without LLM processing
        """
        try:
            results = self.vector_store.similarity_search(question, k=1)
            if results and 'full_action' in results[0].metadata:
                return json.loads(results[0].metadata['full_action'])
            return None
        except Exception as e:
            print(f"Error retrieving action: {e}")
            return None
