import os
from llm_client import LLMManager
from langchain_core.prompts import ChatPromptTemplate

def test_ollama_integration():
    """Test the Ollama integration with Llama 3 model"""
    print("Testing Ollama integration with Llama 3 model...")
    
    try:
        # Initialize LLMManager with Llama 3 model
        llm_manager = LLMManager(model_name="llama3")
        
        # Create a simple prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("human", "{question}")
        ])
        
        # Create a chain
        chain = prompt | llm_manager.llm
        
        # Run the chain with a simple question
        response = chain.invoke({"question": "What is retrieval-augmented generation?"})
        
        print("\nResponse from Llama 3:")
        print(response.content)
        
        return True, "Ollama integration with Llama 3 model works correctly!"
    except Exception as e:
        import traceback
        print(f"Error testing Ollama integration: {str(e)}")
        traceback.print_exc()
        return False, f"Error: {str(e)}"

if __name__ == "__main__":
    success, message = test_ollama_integration()
    print(f"\nTest result: {message}")
