import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the VectorDBTools class
from tools import VectorDBTools

class TestVectorDBTools(unittest.TestCase):
    """
    Test cases for the VectorDBTools class.
    """
    
    @patch('chromadb.HttpClient')
    @patch('langchain_openai.OpenAIEmbeddings')
    @patch('langchain_chroma.Chroma')
    def setUp(self, mock_chroma, mock_embeddings, mock_client):
        """
        Set up the test environment with mocks.
        """
        # Create mock instances
        self.mock_client_instance = mock_client.return_value
        self.mock_embeddings_instance = mock_embeddings.return_value
        self.mock_vector_store = mock_chroma.return_value
        
        # Initialize the VectorDBTools instance
        self.vector_tools = VectorDBTools()
        
        # Replace the vector_store with our mock
        self.vector_tools.vector_store = self.mock_vector_store
        self.vector_tools.client = self.mock_client_instance
        self.vector_tools.embeddings = self.mock_embeddings_instance
    
    def test_search_by_action_id_exact_match(self):
        """
        Test searching by action_id when there's an exact match in the metadata.
        """
        # Set up the mock to return a specific result for get()
        mock_result = {
            'ids': ['doc1', 'doc2'],
            'documents': ['content1', 'content2'],
            'metadatas': [
                {'action_id': 'test_action', 'description': 'Test action description'},
                {'action_id': 'test_action', 'description': 'Another test description'}
            ]
        }
        self.mock_vector_store.get.return_value = mock_result
        
        # Call the method being tested
        results = self.vector_tools.search_by_action_id('test_action')
        
        # Verify the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], 'doc1')
        self.assertEqual(results[0]['content'], 'content1')
        self.assertEqual(results[0]['metadata']['action_id'], 'test_action')
        self.assertEqual(results[1]['id'], 'doc2')
        
        # Verify that get() was called with the correct parameters
        self.mock_vector_store.get.assert_called_once_with(where={'action_id': 'test_action'})
    
    def test_search_by_action_id_similarity_search(self):
        """
        Test searching by action_id when there's no exact match and it falls back to similarity search.
        """
        # Set up the mock to return empty result for get() to trigger similarity search
        self.mock_vector_store.get.return_value = {'ids': []}
        
        # Create mock documents for similarity_search
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Content about test_action"
        mock_doc1.metadata = {'related_action': 'test_action', 'score': 0.95}
        
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Another content about test_action"
        mock_doc2.metadata = {'related_action': 'test_action', 'score': 0.85}
        
        # Set up the mock to return specific results for similarity_search()
        self.mock_vector_store.similarity_search.return_value = [mock_doc1, mock_doc2]
        
        # Call the method being tested
        results = self.vector_tools.search_by_action_id('JLG_S0_A1_LOGIN')
        
        # Verify the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['content'], "Content about JLG_S0_A1_LOGIN")
        self.assertEqual(results[0]['metadata']['related_action'], 'JLG_S0_A1_LOGIN')
        self.assertEqual(results[1]['content'], "Another content about JLG_S0_A1_LOGIN")
        
        # Verify that similarity_search() was called with the correct parameters
        self.mock_vector_store.similarity_search.assert_called_once_with(
            query="action JLG_S0_A1_LOGIN",
            k=5
        )
    
    def test_search_by_action_id_exception_handling(self):
        """
        Test that exceptions are properly handled in search_by_action_id.
        """
        # Set up the mock to raise an exception
        self.mock_vector_store.get.side_effect = Exception("Test exception")
        
        # Call the method being tested
        results = self.vector_tools.search_by_action_id('JLG_S0_A1_LOGIN')
        
        # Verify that an empty list is returned when an exception occurs
        self.assertEqual(results, [])
    
    def test_search_by_action_id_no_results(self):
        """
        Test searching by action_id when no results are found.
        """
        # Set up the mock to return empty results for both get() and similarity_search()
        self.mock_vector_store.get.return_value = {'ids': []}
        self.mock_vector_store.similarity_search.return_value = []
        
        # Call the method being tested
        results = self.vector_tools.search_by_action_id('nonexistent_action')
        
        # Verify that an empty list is returned when no results are found
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()
