import os
import json
from dotenv import load_dotenv
from langchain_core.output_parsers import SimpleJsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings # New import for OpenAI embeddings
from langchain_chroma import Chroma
from llm_client import LLMManager, OllamaLLMManager, OpenAILLMManager
import chromadb

# Load environment variables
load_dotenv()

class RAGChainBuilder:
    """
    A class to build and provide a RAG chain for retrieval augmented generation.
    """

    def __init__(self, llm_type="ollama", model_name="llama3", embedding_type="huggingface"):
        """
        Initializes the RAGChainBuilder's attributes.
        
        Args:
            llm_type (str): Type of LLM to use ('ollama' or 'openai')
            model_name (str): Name of the model to use
            embedding_type (str): Type of embeddings to use ('huggingface' or 'openai')
        """
        try:
            if embedding_type.lower() == "openai":
                # Initialize OpenAI embeddings
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set for OpenAI embeddings.")
                self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="nomic-embed-text")
                print("Initialized OpenAI embeddings")
            else:
                # Default to HuggingFace embeddings
                cache_folder = os.getenv("TRANSFORMERS_CACHE", "./.embeddings_cache")
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    cache_folder=cache_folder,
                    model_kwargs={'device': 'cpu'}  # Ensure CPU usage for better Docker compatibility
                )
                print(f"Initialized HuggingFace embeddings with cache folder: {cache_folder}")
            
            # Initialize ChromaDB client
            print("Connecting to ChromaDB at 3.6.132.24:8000")
            client = chromadb.HttpClient(host='3.6.132.24', port=8000)
            
            # Check if the collection exists
            collection_name = "onboarding_flow_v5"
            collections = client.list_collections()
            collection_names = [c.name for c in collections]
            print(f"Available collections: {collection_names}")
            
            if collection_name not in collection_names:
                print(f"Warning: Collection '{collection_name}' not found in ChromaDB")
            
            # Initialize Chroma vector store with onboarding_flow collection
            self.vector_store = Chroma(
                client=client,
                collection_name=collection_name,
                embedding_function=self.embeddings
            )
            print(f"Successfully connected to ChromaDB collection '{collection_name}'")
        except Exception as e:
            print(f"Error initializing RAGChainBuilder: {str(e)}")
            import traceback
            traceback.print_exc()
            self.vector_store = None
            
        # Initialize the appropriate LLM based on the type
        if llm_type.lower() == "openai":
            llm_manager = OpenAILLMManager(model_name=model_name)
        else:  # Default to Ollama
            llm_manager = OllamaLLMManager(model_name=model_name)
            
        self.llm = llm_manager.llm
        print(f"RAGChainBuilder initialized with {llm_type} model: {model_name}")

    def _format_context(self, docs):
        """Format retrieved documents for the prompt"""
        if not docs:
            return "No relevant actions found."
        
        # Get the most relevant document
        # doc = docs[0]
        # if 'full_action' in doc.metadata:
        #     return doc.metadata['full_action']
        return docs

    
    def run_prompt_with_context(self, query: str, prompt: ChatPromptTemplate):
        """
        Run a custom prompt with retrieved context from ChromaDB. and fetch ui_components and api_details.
        and next_action_id.

        :param query: The natural language question to query vector store.
        :param prompt: ChatPromptTemplate object.
        :return: LLM response python based json structure.
        """
        # "Input to ChatPromptTemplate is missing variables {'query'}.  Expected: ['context', 'query'] Received: ['action_id', 'context']\nNote: if you intended {query} to be part of the string and not a variable, please escape it with double curly braces like: '{{query}}'.\nFor troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/INVALID_PROMPT_INPUT "
        try:
            # Step 1: Retrieve relevant documents from ChromaDB
            results = self.vector_store.similarity_search(query, k=3)

            # Step 2: Format the most relevant result
            context = self._format_context(results)

            # Step 3: Prepare the inputs for the chain
            inputs = {
                "query": query,
                "context": context,
            }

            # Step 4: Run the LLM with the prompt
            chain = (
                prompt
                | self.llm
                |SimpleJsonOutputParser()
            )
            response = chain.invoke(inputs)
            return response

        except Exception as e:
            print(f"Error running prompt with context: {e}")
            return None
    
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
