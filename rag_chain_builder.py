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
        You are an expert assistant for a financial services application called as MiFix which deals in Onboarding and Collections of money in Joint Liabiltity Group. 
        Based on the user's question, you need to return the most relevant workflow step or action.
        
        If the user is asking about a specific workflow step or the onboarding process in general, 
        return the complete workflow step structure as a JSON object.
        
        If the context contains a relevant action but not the complete workflow structure,
        return it as a JSON object with this format: {{ "action": "action_description" }}
        
        If no relevant action or workflow step is found, respond with a helpful message.

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

    def _get_workflow_step(self, step_id):
        """
        Retrieve the complete workflow step structure for a given step_id from ChromaDB.
        """
        try:
            # First, check if we're looking for a direct step_id
            results = self.vector_store.similarity_search(
                f"workflow step {step_id}", 
                k=5,
                filter={"$or": [{"action_id": step_id}, {"step_id": step_id}]}
            )
            
            # If no direct match, try to find if it's an action_id that maps to a step_id
            if not results:
                results = self.vector_store.similarity_search(
                    f"action {step_id}", 
                    k=5
                )
            
            # Process results
            if results:
                for result in results:
                    if 'full_action' in result.metadata:
                        try:
                            return json.loads(result.metadata['full_action'])
                        except json.JSONDecodeError:
                            print(f"Error parsing JSON for step_id {step_id}")
                    
                    # If we have a mapping from action_id to step_id
                    if 'step_id' in result.metadata:
                        mapped_step_id = result.metadata['step_id']
                        # Recursive call with the mapped step_id
                        return self._get_workflow_step(mapped_step_id)
            
            # If we reach here, we couldn't find the step
            print(f"Workflow step not found for ID: {step_id}")
            return None
            
        except Exception as e:
            print(f"Error retrieving workflow step from ChromaDB: {e}")
            return None

    def get_action_directly(self, question: str):
        """
        Get action directly from vector store without LLM processing
        """
        try:
            # Directly check for specific step requests in the question
            lower_question = question.lower()
            
            # Check for specific workflow steps in the question
            if "mobile otp" in lower_question or "otp validation" in lower_question:
                if "validation" in lower_question or "verify" in lower_question:
                    return self._get_workflow_step("mobile_otp_validation")
                else:
                    return self._get_workflow_step("mobile_otp_generation")
            elif "aadhaar" in lower_question or "aadhar" in lower_question or "biometric" in lower_question:
                return self._get_workflow_step("aadhar_biometric")
            
            # If no direct match, search the vector store
            results = self.vector_store.similarity_search(question, k=3)
            
            # Check if the query is about the onboarding process or workflow steps
            if any(kw in lower_question for kw in ["onboarding", "process", "workflow", "step", "otp", "mobile", "aadhaar", "aadhar", "biometric"]):
                # Try to find a specific step in the results
                for result in results:
                    action_id = result.metadata.get('action_id')
                    if action_id:
                        workflow_step = self._get_workflow_step(action_id)
                        if workflow_step:
                            return workflow_step
                
                # If no specific step found but query is about onboarding, return a general onboarding flow
                if "onboarding" in lower_question or "process" in lower_question:
                    # Get the onboarding flow overview from ChromaDB
                    try:
                        # First try with exact filter
                        flow_results = self.vector_store.similarity_search(
                            "onboarding flow overview process", 
                            k=1,
                            filter={"action_id": "onboarding_flow"}
                        )
                        
                        # If no results, try without filter
                        if not flow_results:
                            flow_results = self.vector_store.similarity_search(
                                "onboarding flow overview process", 
                                k=1
                            )
                        
                        if flow_results and 'full_action' in flow_results[0].metadata:
                            try:
                                return json.loads(flow_results[0].metadata['full_action'])
                            except json.JSONDecodeError:
                                print("Error parsing onboarding flow JSON")
                                # Continue to next approach if parsing fails
                        
                        # If we have results but no full_action, try to construct from metadata
                        if flow_results:
                            action_id = flow_results[0].metadata.get('action_id')
                            description = flow_results[0].metadata.get('description')
                            if action_id and description:
                                return {
                                    "action": f"{action_id}: {description}",
                                    "message": "Retrieved onboarding flow information from database"
                                }
                    except Exception as e:
                        print(f"Error retrieving onboarding flow: {e}")
                    
                    # If we couldn't get the flow from ChromaDB, query for individual steps
                    # and try to construct the flow
                    try:
                        # Get all workflow steps
                        all_steps = self.vector_store.similarity_search(
                            "all onboarding workflow steps",
                            k=20  # Try to get all steps
                        )
                        
                        if all_steps:
                            workflow_steps = []
                            step_ids = set()
                            
                            for step in all_steps:
                                step_id = step.metadata.get('step_id')
                                step_title = step.metadata.get('step_title')
                                description = step.metadata.get('description')
                                
                                if step_id and step_id not in step_ids and step_title and description:
                                    step_ids.add(step_id)
                                    workflow_steps.append({
                                        "step": str(len(workflow_steps) + 1),
                                        "name": step_title,
                                        "description": description
                                    })
                            
                            if workflow_steps:
                                return {
                                    "step_id": "onboarding_flow",
                                    "step_title": "Onboarding Process",
                                    "step_description": "Complete onboarding flow for microfinance clients",
                                    "workflow_steps": workflow_steps,
                                    "note": "Constructed from available workflow steps in database"
                                }
                    except Exception as e:
                        print(f"Error constructing workflow from steps: {e}")
                    
                    # If we still couldn't get the flow, return a generic response
                    return {
                        "action": "onboarding_flow: The onboarding flow information could not be retrieved from the database",
                        "message": "Please ensure the onboarding flow data is properly uploaded to ChromaDB"
                    }
            
            if results:
                # Check if we have a full action in metadata
                if 'full_action' in results[0].metadata:
                    try:
                        return json.loads(results[0].metadata['full_action'])
                    except json.JSONDecodeError:
                        # If not valid JSON, return as is
                        return {"action": results[0].metadata['full_action']}
                
                # Otherwise, create a simple action response
                action_id = results[0].metadata.get('action_id')
                description = results[0].metadata.get('description')
                if action_id and description:
                    return {
                        "action": f"{action_id}: {description}"
                    }
                
                # Fallback to the document content
                return {
                    "action": results[0].page_content
                }
                
            return None
        except Exception as e:
            print(f"Error retrieving action: {e}")
            return None
