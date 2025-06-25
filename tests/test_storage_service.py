import unittest
import sys
import os
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.storage_service import StorageService
from storage.metadata_interface import user_metadata, customer_metadata, user_customer_metadata, customer_stage_metadata

class TestStorageService(unittest.TestCase):
    """Test cases for the StorageService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock objects for DynamoDB and Redis
        self.dynamo_mock = MagicMock()
        self.redis_mock = MagicMock()
        
        # Patch boto3 and redis
        self.boto3_patcher = patch('storage.storage_service.boto3')
        self.redis_patcher = patch('storage.storage_service.redis')
        
        # Start patchers
        self.mock_boto3 = self.boto3_patcher.start()
        self.mock_redis = self.redis_patcher.start()
        
        # Configure mocks
        self.mock_boto3.resource.return_value.Table.return_value = self.dynamo_mock
        self.mock_redis.Redis.return_value = self.redis_mock
        
        # Create storage service instance
        self.storage = StorageService()
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop patchers
        self.boto3_patcher.stop()
        self.redis_patcher.stop()
    
    def test_save_user(self):
        """Test saving a user"""
        # Create test user
        user = user_metadata()
        user.user_id = "test_user_id"
        user.user_email = "test@example.com"
        user.user_name = "Test User"
        user.user_password_hash = "hashed_password"
        
        # Configure mock
        self.dynamo_mock.put_item.return_value = {}
        self.redis_mock.set.return_value = True
        
        # Call method
        result = self.storage.save_user(user)
        
        # Assertions
        self.assertTrue(result)
        self.dynamo_mock.put_item.assert_called_once()
        self.assertEqual(self.redis_mock.set.call_count, 2)  # One for user, one for email index
    
    def test_get_user_by_id(self):
        """Test getting a user by ID"""
        # Configure mock for cache miss, DB hit
        self.redis_mock.get.return_value = None
        self.dynamo_mock.get_item.return_value = {
            'Item': {
                'userId': 'test_user_id',
                'userEmail': 'test@example.com',
                'userName': 'Test User',
                'userPasswordHash': 'hashed_password',
                'createdAt': '2023-01-01T00:00:00Z',
                'updatedAt': '2023-01-01T00:00:00Z'
            }
        }
        
        # Call method
        user = self.storage.get_user_by_id('test_user_id')
        
        # Assertions
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, 'test_user_id')
        self.assertEqual(user.user_email, 'test@example.com')
        self.dynamo_mock.get_item.assert_called_once()
        self.redis_mock.set.assert_called()  # Should cache the result
    
    def test_get_user_by_email(self):
        """Test getting a user by email"""
        # Configure mock for cache hit
        self.redis_mock.get.side_effect = [
            'test_user_id',  # First call for email lookup returns user_id
            '{"user_id": "test_user_id", "user_email": "test@example.com"}'  # Second call for user data
        ]
        
        # Call method
        user = self.storage.get_user_by_email('test@example.com')
        
        # Assertions
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, 'test_user_id')
        self.dynamo_mock.query.assert_not_called()  # Should not hit DB
    
    def test_save_customer(self):
        """Test saving a customer"""
        # Create test customer
        customer = customer_metadata()
        customer.customer_id = "test_customer_id"
        customer.customer_name = "Test Customer"
        customer.mobile_number = "1234567890"
        
        # Configure mock
        self.dynamo_mock.put_item.return_value = {}
        self.redis_mock.set.return_value = True
        
        # Call method
        result = self.storage.save_customer(customer)
        
        # Assertions
        self.assertTrue(result)
        self.dynamo_mock.put_item.assert_called_once()
        self.assertEqual(self.redis_mock.set.call_count, 2)  # One for customer, one for mobile index
    
    def test_user_customer_relation(self):
        """Test saving and retrieving user-customer relationship"""
        # Create test relation
        relation = user_customer_metadata()
        relation.user_id = "test_user_id"
        relation.customer_id = "test_customer_id"
        relation.user_customer_id = "test_relation_id"
        
        # Configure mocks
        self.dynamo_mock.put_item.return_value = {}
        self.redis_mock.set.return_value = True
        self.redis_mock.sadd.return_value = 1
        self.redis_mock.expire.return_value = True
        
        # Save relation
        result = self.storage.save_user_customer_relation(relation)
        self.assertTrue(result)
        
        # Test get user customers
        self.redis_mock.smembers.return_value = {"test_customer_id"}
        self.redis_mock.get.return_value = '{"customer_id": "test_customer_id", "customer_name": "Test Customer"}'
        
        customers = self.storage.get_user_customers("test_user_id")
        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0].customer_id, "test_customer_id")
    
    def test_customer_stage(self):
        """Test saving and retrieving customer stage data"""
        # Create test stage
        stage = customer_stage_metadata()
        stage.customer_id = "test_customer_id"
        stage.stage_id = "test_stage_id"
        stage.stage_name = "Test Stage"
        stage.stage_data = {"key": "value"}
        
        # Configure mocks
        self.dynamo_mock.put_item.return_value = {}
        self.redis_mock.set.return_value = True
        self.redis_mock.sadd.return_value = 1
        self.redis_mock.expire.return_value = True
        
        # Save stage
        result = self.storage.save_customer_stage(stage)
        self.assertTrue(result)
        
        # Test get stage
        self.redis_mock.get.return_value = '{"customer_id": "test_customer_id", "stage_id": "test_stage_id", "stage_name": "Test Stage", "stage_data": {"key": "value"}}'
        
        retrieved_stage = self.storage.get_customer_stage("test_customer_id", "test_stage_id")
        self.assertIsNotNone(retrieved_stage)
        self.assertEqual(retrieved_stage.stage_id, "test_stage_id")
        self.assertEqual(retrieved_stage.stage_data.get("key"), "value")

if __name__ == '__main__':
    unittest.main()
