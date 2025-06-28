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
            collection_name = "onboarding_flow_v16"
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
        """Format retrieved documents for the prompt with complete structured data"""
        if not docs:
            return "No relevant actions found."
        
        formatted_context = {
            "retrieved_documents": [],
            "total_documents": len(docs)
        }
        
        for doc in docs:
            doc_data = {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            
            # Check if this document contains full_action metadata with complete UI schema
            if 'full_action' in doc.metadata:
                try:
                    # Parse the full_action JSON if it's a string
                    full_action = doc.metadata['full_action']
                    if isinstance(full_action, str):
                        full_action = json.loads(full_action)
                    
                    doc_data["type"] = "complete_ui_schema"
                    doc_data["parsed_action"] = full_action
                    
                except json.JSONDecodeError:
                    doc_data["type"] = "ui_component_data"
            else:
                # Try to parse the page content as JSON for UI components
                try:
                    parsed_content = json.loads(doc.page_content)
                    doc_data["type"] = "ui_component_data"
                    doc_data["parsed_content"] = parsed_content
                except json.JSONDecodeError:
                    doc_data["type"] = "text_content"
            
            formatted_context["retrieved_documents"].append(doc_data)
        
        return json.dumps(formatted_context, indent=2)

    def run_prompt_with_context(self, query: str, prompt: ChatPromptTemplate, variables: dict = None):
        """
        Run a custom prompt with retrieved context from ChromaDB. and fetch ui_components and api_details.
        and next_action_id.

        :param query: The natural language question to query vector store.
        :param prompt: ChatPromptTemplate object.
        :return: LLM response python based json structure.
        """
        try:
            # Step 1: Retrieve relevant documents from ChromaDB with multiple search strategies
            print(f"Searching for documents related to: {query}")
            
            # Primary search for the current action
            results = self.vector_store.similarity_search(query, k=5)
            print(f"Primary search found {len(results)} documents")
            
            # Additional searches to ensure we get next action UI components
            additional_searches = [
                f"ui_schema {query}",
                f"video consent ui components",
                f"mobile verification ui components", 
                f"ui_video_consent_001",
                f"ui_mobile_verification_001",
                "next_success_action_id"
            ]
            
            all_results = results.copy()
            for search_term in additional_searches:
                try:
                    extra_results = self.vector_store.similarity_search(search_term, k=3)
                    print(f"Additional search '{search_term}' found {len(extra_results)} documents")
                    # Add unique results only
                    for result in extra_results:
                        if result not in all_results:
                            all_results.append(result)
                except Exception as e:
                    print(f"Additional search failed for '{search_term}': {e}")
                    continue
            
            print(f"Total unique documents retrieved: {len(all_results)}")

            # Step 2: Format the comprehensive results
            context = self._format_context(all_results)

            # Step 3: Prepare the inputs for the chain
            inputs = {
                "query": query,
                "context": context,
            }
            
            # Merge variables dictionary if provided
            if variables:
                inputs.update(variables)

            # Step 4: Run the LLM with the prompt
            chain = (
                prompt
                | self.llm
                |SimpleJsonOutputParser()
            )
            response = chain.invoke(inputs)
            
            # Debug logging
            print(f"LLM Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
            if isinstance(response, dict) and 'next_action_ui_components' in response:
                next_components = response['next_action_ui_components']
                print(f"Next action UI components count: {len(next_components) if isinstance(next_components, list) else 'Not a list'}")
            
            return response

        except Exception as e:
            print(f"Error running prompt with context: {e}")
            import traceback
            traceback.print_exc()
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

    def get_ui_components_by_action_id(self, action_id: str):
        """
        Retrieve UI components specifically for a given action_id
        
        :param action_id: The action ID to search for (e.g., 'video-consent', 'select-flow')
        :return: List of UI components for the specified action ONLY
        """
        try:
            print(f"Searching for UI components for action_id: {action_id}")
            
            # Generate the expected ui_id pattern
            expected_ui_id = f"ui_{action_id.replace('-', '_')}_001"
            print(f"Looking for UI schema with ui_id: {expected_ui_id}")
            
            # Search strategies - prioritize exact ui_id match
            search_queries = [
                expected_ui_id,  # e.g., ui_select_flow_001
                f"UI SCHEMA: {expected_ui_id}",
                f"{action_id} screen ui components",
                f"{action_id} ui schema"
            ]
            
            best_match = None
            for query in search_queries:
                try:
                    results = self.vector_store.similarity_search(query, k=5)
                    print(f"Query '{query}' found {len(results)} documents")
                    
                    for result in results:
                        metadata = result.metadata
                        content = result.page_content
                        
                        # Priority 1: UI schema document with exact id match
                        if metadata.get('type') == 'ui_schema' and metadata.get('id') == expected_ui_id:
                            print(f"Found UI schema document with exact id match: {expected_ui_id}")
                            best_match = result
                            break
                        
                        # Priority 2: UI schema document with matching ui_id
                        elif metadata.get('type') == 'ui_schema' and 'full_ui_schema' in metadata:
                            try:
                                schema_str = metadata['full_ui_schema']
                                if isinstance(schema_str, str):
                                    schema = json.loads(schema_str)
                                    if schema.get('id') == expected_ui_id:
                                        print(f"Found UI schema with matching id in full_ui_schema: {expected_ui_id}")
                                        best_match = result
                                        break
                            except (json.JSONDecodeError, KeyError):
                                pass
                        
                        # Priority 3: Action document with exact ui_id match (fallback)
                        elif metadata.get('ui_id') == expected_ui_id or metadata.get('screen_id') == f"{action_id.replace('-', '_')}_screen":
                            print(f"Found action document with ui_id match: {metadata.get('ui_id', 'unknown')}")
                            if not best_match:  # Only use if no UI schema found
                                best_match = result
                        
                        # Priority 4: Check 'id' field in metadata (for other documents)
                        elif metadata.get('id') == expected_ui_id:
                            print(f"Found document with exact id match: {metadata.get('id', 'unknown')}")
                            if not best_match:  # Only use if no better match found
                                best_match = result
                        
                        # Priority 5: Content contains the expected ui_id
                        elif expected_ui_id in content and 'ui_components' in content:
                            print(f"Found content with expected ui_id pattern")
                            if not best_match:  # Only use if no better match found
                                best_match = result
                    
                    if best_match:
                        break
                        
                except Exception as e:
                    print(f"Search query '{query}' failed: {e}")
                    continue
            
            if not best_match:
                print(f"No UI components found for action_id: {action_id}")
                return []
            
            # Extract UI components from the best match
            try:
                metadata = best_match.metadata
                content = best_match.page_content
                
                # Method 1: Check full_ui_schema in metadata
                if 'full_ui_schema' in metadata:
                    ui_schema = metadata['full_ui_schema']
                    if isinstance(ui_schema, str):
                        ui_schema = json.loads(ui_schema)
                    
                    # Return the ui_components array if it exists
                    if isinstance(ui_schema, dict) and 'ui_components' in ui_schema:
                        components = ui_schema['ui_components']
                        print(f"Successfully extracted {len(components)} UI components from metadata for {action_id}")
                        return components
                    elif isinstance(ui_schema, list):
                        print(f"Successfully extracted {len(ui_schema)} UI components from metadata for {action_id}")
                        return ui_schema
                
                # Method 2: Parse JSON from page content
                if content.strip().startswith('{') or content.strip().startswith('['):
                    try:
                        parsed_content = json.loads(content)
                        
                        # If it's a complete UI schema object
                        if isinstance(parsed_content, dict):
                            if 'ui_components' in parsed_content:
                                components = parsed_content['ui_components']
                                print(f"Successfully parsed {len(components)} UI components from content for {action_id}")
                                return components
                            # If the entire object is the UI schema
                            elif 'id' in parsed_content and 'component_type' in parsed_content:
                                print(f"Found single UI component in content for {action_id}")
                                return [parsed_content]
                        
                        # If it's directly an array of components
                        elif isinstance(parsed_content, list):
                            print(f"Successfully parsed {len(parsed_content)} UI components from content array for {action_id}")
                            return parsed_content
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing failed for {action_id}: {e}")
                
                # Method 3: Extract from text content (fallback)
                print(f"Attempting text extraction for {action_id}")
                # This is a fallback - in practice, UI components should be in structured format
                return []
                
            except Exception as e:
                print(f"Error extracting UI components for {action_id}: {e}")
                return []
            
        except Exception as e:
            print(f"Error in get_ui_components_by_action_id for {action_id}: {e}")
            return []
