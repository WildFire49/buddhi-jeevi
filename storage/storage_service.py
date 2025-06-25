import boto3
import redis
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
import os
from dotenv import load_dotenv

# Import metadata classes
from .metadata_interface import (
    user_metadata,
    customer_metadata,
    user_customer_metadata,
    customer_stage_metadata
)

# Load environment variables
load_dotenv()

# DynamoDB Configuration
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'ap-south-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
TABLE_NAME = os.getenv('DYNAMODB_TABLE', 'OnboardingSystem')
MOBILE_INDEX_NAME = 'MobileNumberIndex'
table = dynamodb.Table(TABLE_NAME)

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_TTL = int(os.getenv('REDIS_TTL', 3600))  # Default TTL: 1 hour

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

class StorageService:
    """
    Service class to handle storage operations for metadata objects
    in both DynamoDB (permanent) and Redis (cache)
    """
    
    @staticmethod
    def _generate_timestamp() -> str:
        """Generate ISO format timestamp"""
        return datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def _generate_id(prefix: str = '') -> str:
        """Generate a unique ID with optional prefix"""
        return f"{prefix}{uuid.uuid4()}"
    
    @staticmethod
    def _serialize_to_json(data: Any) -> str:
        """Convert data to JSON string"""
        return json.dumps(data, default=lambda o: o.__dict__)
    
    @staticmethod
    def _deserialize_from_json(json_str: str, target_class: Any) -> Any:
        """Convert JSON string back to object"""
        data = json.loads(json_str)
        obj = target_class()
        for key, value in data.items():
            setattr(obj, key, value)
        return obj
    
    # ==================== USER OPERATIONS ====================
    
    def save_user(self, user: user_metadata) -> bool:
        """
        Save user data to DynamoDB and cache in Redis
        
        Args:
            user: User metadata object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate user_id if not provided
            if not hasattr(user, 'user_id') or not user.user_id:
                user.user_id = self._generate_id('usr_')
                
            # Set creation timestamp if not provided
            if not hasattr(user, 'user_created_at') or not user.user_created_at:
                user.user_created_at = self._generate_timestamp()
                
            # Create DynamoDB item
            user_pk = f"USER#{user.user_id}"
            
            # Save to DynamoDB
            table.put_item(
                Item={
                    'PK': user_pk,
                    'SK': 'METADATA',
                    'userId': user.user_id,
                    'userName': getattr(user, 'user_name', ''),
                    'userEmail': getattr(user, 'user_email', ''),
                    'userMobile': getattr(user, 'user_mobile', ''),
                    'passwordHash': getattr(user, 'user_password', ''),  # Should be hashed before storage
                    'createdAt': user.user_created_at
                }
            )
            
            # Cache in Redis
            redis_key = f"user:{user.user_id}"
            redis_client.set(
                redis_key, 
                self._serialize_to_json(user),
                ex=REDIS_TTL
            )
            
            return True
            
        except Exception as e:
            print(f"Error saving user: {e}")
            return False
    
    def get_user_by_id(self, user_id: str) -> Optional[user_metadata]:
        """
        Get user by ID, first checking Redis cache then DynamoDB
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[user_metadata]: User object if found, None otherwise
        """
        try:
            # Try to get from Redis first
            redis_key = f"user:{user_id}"
            cached_user = redis_client.get(redis_key)
            
            if cached_user:
                # User found in cache
                return self._deserialize_from_json(cached_user, user_metadata)
            
            # Not in cache, get from DynamoDB
            user_pk = f"USER#{user_id}"
            response = table.get_item(Key={'PK': user_pk, 'SK': 'METADATA'})
            
            if 'Item' in response:
                # Create user object from DynamoDB item
                item = response['Item']
                user = user_metadata()
                user.user_id = item.get('userId')
                user.user_name = item.get('userName')
                user.user_email = item.get('userEmail')
                user.user_mobile = item.get('userMobile')
                user.user_password = item.get('passwordHash')  # This is the hashed password
                user.user_created_at = item.get('createdAt')
                
                # Cache in Redis for future requests
                redis_client.set(
                    redis_key, 
                    self._serialize_to_json(user),
                    ex=REDIS_TTL
                )
                
                return user
            
            return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
            
    def get_user_by_email(self, email: str) -> Optional[user_metadata]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            Optional[user_metadata]: User object if found, None otherwise
        """
        try:
            # Try to get from Redis first using email index
            redis_key = f"user:email:{email}"
            cached_user_id = redis_client.get(redis_key)
            
            if cached_user_id:
                # Get the full user using the ID
                return self.get_user_by_id(cached_user_id)
            
            # Not in cache, query DynamoDB using GSI (requires email GSI to be set up)
            # For now, we'll scan the table (not efficient for production)
            response = table.scan(
                FilterExpression="userEmail = :email",
                ExpressionAttributeValues={
                    ":email": email
                }
            )
            
            for item in response.get('Items', []):
                if item.get('userEmail') == email:
                    user_id = item.get('userId')
                    
                    # Cache the email to user_id mapping
                    redis_client.set(redis_key, user_id, ex=REDIS_TTL)
                    
                    # Return the full user
                    return self.get_user_by_id(user_id)
            
            return None
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
            
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from both DynamoDB and Redis cache
        
        Args:
            user_id: User ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the user first to have email for cache invalidation
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
                
            # Delete from DynamoDB
            user_pk = f"USER#{user_id}"
            table.delete_item(Key={'PK': user_pk, 'SK': 'METADATA'})
            
            # Delete from Redis cache
            redis_client.delete(f"user:{user_id}")
            
            # Delete email index if exists
            if hasattr(user, 'user_email') and user.user_email:
                redis_client.delete(f"user:email:{user.user_email}")
                
            return True
            
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
            
    # ==================== CUSTOMER OPERATIONS ====================
    
    def save_customer(self, customer: customer_metadata) -> bool:
        """
        Save customer data to DynamoDB and cache in Redis
        
        Args:
            customer: Customer metadata object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate customer_id if not provided
            if not hasattr(customer, 'customer_id') or not customer.customer_id:
                customer.customer_id = self._generate_id('cust_')
                
            # Set timestamps if not provided
            current_time = self._generate_timestamp()
            if not hasattr(customer, 'customer_created_at') or not customer.customer_created_at:
                customer.customer_created_at = current_time
            if not hasattr(customer, 'customer_updated_at') or not customer.customer_updated_at:
                customer.customer_updated_at = current_time
                
            # Set default is_deleted flag if not provided
            if not hasattr(customer, 'is_deleted'):
                customer.is_deleted = False
                
            # Create DynamoDB item
            cust_pk = f"CUST#{customer.customer_id}"
            
            # Save to DynamoDB
            item = {
                'PK': cust_pk,
                'SK': 'METADATA',
                'customerId': customer.customer_id,
                'customerName': getattr(customer, 'customer_name', ''),
                'mobileNumber': getattr(customer, 'mobile_number', ''),
                'createdAt': customer.customer_created_at,
                'updatedAt': customer.customer_updated_at,
                'isDeleted': customer.is_deleted
            }
            
            table.put_item(Item=item)
            
            # Cache in Redis
            redis_key = f"customer:{customer.customer_id}"
            redis_client.set(
                redis_key, 
                self._serialize_to_json(customer),
                ex=REDIS_TTL
            )
            
            # Also index by mobile number for quick lookups
            if hasattr(customer, 'mobile_number') and customer.mobile_number:
                mobile_key = f"customer:mobile:{customer.mobile_number}"
                redis_client.set(mobile_key, customer.customer_id, ex=REDIS_TTL)
            
            return True
            
        except Exception as e:
            print(f"Error saving customer: {e}")
            return False
    
    def get_customer_by_id(self, customer_id: str) -> Optional[customer_metadata]:
        """
        Get customer by ID, first checking Redis cache then DynamoDB
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Optional[customer_metadata]: Customer object if found, None otherwise
        """
        try:
            # Try to get from Redis first
            redis_key = f"customer:{customer_id}"
            cached_customer = redis_client.get(redis_key)
            
            if cached_customer:
                # Customer found in cache
                return self._deserialize_from_json(cached_customer, customer_metadata)
            
            # Not in cache, get from DynamoDB
            cust_pk = f"CUST#{customer_id}"
            response = table.get_item(Key={'PK': cust_pk, 'SK': 'METADATA'})
            
            if 'Item' in response:
                # Create customer object from DynamoDB item
                item = response['Item']
                customer = customer_metadata()
                customer.customer_id = item.get('customerId')
                customer.customer_name = item.get('customerName')
                customer.mobile_number = item.get('mobileNumber')
                customer.customer_created_at = item.get('createdAt')
                customer.customer_updated_at = item.get('updatedAt')
                customer.is_deleted = item.get('isDeleted', False)
                
                # Cache in Redis for future requests
                redis_client.set(
                    redis_key, 
                    self._serialize_to_json(customer),
                    ex=REDIS_TTL
                )
                
                # Also index by mobile number for quick lookups
                if customer.mobile_number:
                    mobile_key = f"customer:mobile:{customer.mobile_number}"
                    redis_client.set(mobile_key, customer.customer_id, ex=REDIS_TTL)
                
                return customer
            
            return None
            
        except Exception as e:
            print(f"Error getting customer: {e}")
            return None
    
    def get_customer_by_mobile(self, mobile_number: str) -> Optional[customer_metadata]:
        """
        Get customer by mobile number
        
        Args:
            mobile_number: Customer mobile number
            
        Returns:
            Optional[customer_metadata]: Customer object if found, None otherwise
        """
        try:
            # Try to get from Redis first using mobile index
            redis_key = f"customer:mobile:{mobile_number}"
            cached_customer_id = redis_client.get(redis_key)
            
            if cached_customer_id:
                # Get the full customer using the ID
                return self.get_customer_by_id(cached_customer_id)
            
            # Not in cache, query DynamoDB using GSI
            response = table.query(
                IndexName=MOBILE_INDEX_NAME,
                KeyConditionExpression="mobileNumber = :mobile",
                ExpressionAttributeValues={
                    ":mobile": mobile_number
                }
            )
            
            items = response.get('Items', [])
            if items:
                customer_id = items[0].get('customerId')
                
                # Cache the mobile to customer_id mapping
                redis_client.set(redis_key, customer_id, ex=REDIS_TTL)
                
                # Return the full customer
                return self.get_customer_by_id(customer_id)
            
            return None
            
        except Exception as e:
            print(f"Error getting customer by mobile: {e}")
            return None
    
    def update_customer(self, customer: customer_metadata) -> bool:
        """
        Update customer data in DynamoDB and Redis cache
        
        Args:
            customer: Customer metadata object with updated fields
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if customer exists
            if not hasattr(customer, 'customer_id') or not customer.customer_id:
                print("Cannot update customer: No customer_id provided")
                return False
            
            # Get existing customer to preserve fields not in the update
            existing_customer = self.get_customer_by_id(customer.customer_id)
            if not existing_customer:
                print(f"Cannot update customer: Customer with ID {customer.customer_id} not found")
                return False
            
            # Update timestamp
            customer.customer_updated_at = self._generate_timestamp()
            
            # Merge existing and new data
            for attr in dir(customer):
                if not attr.startswith('__') and hasattr(customer, attr):
                    value = getattr(customer, attr)
                    if value is not None:
                        setattr(existing_customer, attr, value)
            
            # Save the updated customer
            return self.save_customer(existing_customer)
            
        except Exception as e:
            print(f"Error updating customer: {e}")
            return False
    
    def delete_customer(self, customer_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a customer (soft delete by default, hard delete optional)
        
        Args:
            customer_id: Customer ID to delete
            hard_delete: If True, physically remove from DB; if False, mark as deleted
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the customer first
            customer = self.get_customer_by_id(customer_id)
            
            if not customer:
                return False
            
            if hard_delete:
                # Hard delete - remove from DynamoDB
                cust_pk = f"CUST#{customer_id}"
                table.delete_item(Key={'PK': cust_pk, 'SK': 'METADATA'})
            else:
                # Soft delete - mark as deleted
                customer.is_deleted = True
                customer.customer_updated_at = self._generate_timestamp()
                
                # Update in DynamoDB
                cust_pk = f"CUST#{customer_id}"
                table.update_item(
                    Key={'PK': cust_pk, 'SK': 'METADATA'},
                    UpdateExpression="SET isDeleted = :deleted, updatedAt = :updated",
                    ExpressionAttributeValues={
                        ":deleted": True,
                        ":updated": customer.customer_updated_at
                    }
                )
            
            # Delete from Redis cache
            redis_client.delete(f"customer:{customer_id}")
            
            # Delete mobile index if exists
            if hasattr(customer, 'mobile_number') and customer.mobile_number:
                redis_client.delete(f"customer:mobile:{customer.mobile_number}")
                
            return True
            
        except Exception as e:
            print(f"Error deleting customer: {e}")
            return False
            
    # ==================== USER-CUSTOMER RELATIONSHIP OPERATIONS ====================
    
    def save_user_customer_relation(self, relation: user_customer_metadata) -> bool:
        """
        Save user-customer relationship data to DynamoDB and cache in Redis
        
        Args:
            relation: User-customer relationship metadata object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check required fields
            if not hasattr(relation, 'user_id') or not relation.user_id:
                print("Cannot save relation: No user_id provided")
                return False
                
            if not hasattr(relation, 'customer_id') or not relation.customer_id:
                print("Cannot save relation: No customer_id provided")
                return False
            
            # Generate relation ID if not provided
            if not hasattr(relation, 'user_customer_id') or not relation.user_customer_id:
                relation.user_customer_id = self._generate_id('rel_')
                
            # Set timestamps if not provided
            current_time = self._generate_timestamp()
            if not hasattr(relation, 'user_customer_created_at') or not relation.user_customer_created_at:
                relation.user_customer_created_at = current_time
            if not hasattr(relation, 'user_customer_updated_at') or not relation.user_customer_updated_at:
                relation.user_customer_updated_at = current_time
                
            # Set default is_deleted flag if not provided
            if not hasattr(relation, 'is_deleted'):
                relation.is_deleted = False
                
            # Create DynamoDB item
            user_pk = f"USER#{relation.user_id}"
            cust_pk = f"CUST#{relation.customer_id}"
            
            # Save to DynamoDB
            item = {
                'PK': user_pk,
                'SK': cust_pk,
                'userId': relation.user_id,
                'customerId': relation.customer_id,
                'relationId': relation.user_customer_id,
                'createdAt': relation.user_customer_created_at,
                'updatedAt': relation.user_customer_updated_at,
                'isDeleted': relation.is_deleted
            }
            
            table.put_item(Item=item)
            
            # Cache in Redis
            redis_key = f"relation:{relation.user_customer_id}"
            redis_client.set(
                redis_key, 
                self._serialize_to_json(relation),
                ex=REDIS_TTL
            )
            
            # Also index by user_id and customer_id for quick lookups
            user_rel_key = f"user:{relation.user_id}:customers"
            cust_rel_key = f"customer:{relation.customer_id}:users"
            
            # Add to user's customer list
            redis_client.sadd(user_rel_key, relation.customer_id)
            redis_client.expire(user_rel_key, REDIS_TTL)
            
            # Add to customer's user list
            redis_client.sadd(cust_rel_key, relation.user_id)
            redis_client.expire(cust_rel_key, REDIS_TTL)
            
            return True
            
        except Exception as e:
            print(f"Error saving user-customer relation: {e}")
            return False
    
    def get_user_customers(self, user_id: str) -> List[customer_metadata]:
        """
        Get all customers associated with a user
        
        Args:
            user_id: User ID
            
        Returns:
            List[customer_metadata]: List of customer objects
        """
        try:
            customers = []
            
            # Try to get from Redis first
            user_rel_key = f"user:{user_id}:customers"
            cached_customer_ids = redis_client.smembers(user_rel_key)
            
            if cached_customer_ids:
                # Get each customer from cache or DB
                for customer_id in cached_customer_ids:
                    customer = self.get_customer_by_id(customer_id)
                    if customer and not customer.is_deleted:
                        customers.append(customer)
                return customers
            
            # Not in cache, query DynamoDB
            user_pk = f"USER#{user_id}"
            response = table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": user_pk,
                    ":sk_prefix": "CUST#"
                }
            )
            
            # Process results
            for item in response.get('Items', []):
                customer_id = item.get('customerId')
                if customer_id:
                    # Add to Redis set for future lookups
                    redis_client.sadd(user_rel_key, customer_id)
                    
                    # Get the full customer
                    customer = self.get_customer_by_id(customer_id)
                    if customer and not customer.is_deleted:
                        customers.append(customer)
            
            # Set expiry on the Redis set
            if customers:
                redis_client.expire(user_rel_key, REDIS_TTL)
                
            return customers
            
        except Exception as e:
            print(f"Error getting user's customers: {e}")
            return []
    
    def get_customer_users(self, customer_id: str) -> List[user_metadata]:
        """
        Get all users associated with a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List[user_metadata]: List of user objects
        """
        try:
            users = []
            
            # Try to get from Redis first
            cust_rel_key = f"customer:{customer_id}:users"
            cached_user_ids = redis_client.smembers(cust_rel_key)
            
            if cached_user_ids:
                # Get each user from cache or DB
                for user_id in cached_user_ids:
                    user = self.get_user_by_id(user_id)
                    if user:
                        users.append(user)
                return users
            
            # Not in cache, query DynamoDB
            cust_sk = f"CUST#{customer_id}"
            response = table.query(
                IndexName="SK-PK-index",  # This assumes you have a GSI on SK and PK
                KeyConditionExpression="SK = :sk",
                ExpressionAttributeValues={
                    ":sk": cust_sk
                }
            )
            
            # Process results
            for item in response.get('Items', []):
                user_id = item.get('userId')
                if user_id:
                    # Add to Redis set for future lookups
                    redis_client.sadd(cust_rel_key, user_id)
                    
                    # Get the full user
                    user = self.get_user_by_id(user_id)
                    if user:
                        users.append(user)
            
            # Set expiry on the Redis set
            if users:
                redis_client.expire(cust_rel_key, REDIS_TTL)
                
            return users
            
        except Exception as e:
            print(f"Error getting customer's users: {e}")
            return []
            
    # ==================== CUSTOMER STAGE OPERATIONS ====================
    
    def save_customer_stage(self, stage: customer_stage_metadata) -> bool:
        """
        Save customer stage data to DynamoDB and cache in Redis
        
        Args:
            stage: Customer stage metadata object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check required fields
            if not hasattr(stage, 'customer_id') or not stage.customer_id:
                print("Cannot save stage: No customer_id provided")
                return False
                
            if not hasattr(stage, 'stage_id') or not stage.stage_id:
                print("Cannot save stage: No stage_id provided")
                return False
            
            # Set timestamps if not provided
            current_time = self._generate_timestamp()
            if not hasattr(stage, 'stage_created_at') or not stage.stage_created_at:
                stage.stage_created_at = current_time
            if not hasattr(stage, 'stage_updated_at') or not stage.stage_updated_at:
                stage.stage_updated_at = current_time
                
            # Set default is_deleted flag if not provided
            if not hasattr(stage, 'is_deleted'):
                stage.is_deleted = False
                
            # Create DynamoDB item
            cust_pk = f"CUST#{stage.customer_id}"
            stage_sk = f"STAGE#{stage.stage_id}"
            
            # Prepare stage data
            stage_data = getattr(stage, 'stage_data', {})
            if not stage_data:
                stage_data = {}
                
            # Save to DynamoDB
            item = {
                'PK': cust_pk,
                'SK': stage_sk,
                'customerId': stage.customer_id,
                'stageId': stage.stage_id,
                'stageName': getattr(stage, 'stage_name', ''),
                'createdAt': stage.stage_created_at,
                'updatedAt': stage.stage_updated_at,
                'isDeleted': stage.is_deleted,
                'stageData': stage_data
            }
            
            table.put_item(Item=item)
            
            # Cache in Redis
            redis_key = f"customer:{stage.customer_id}:stage:{stage.stage_id}"
            redis_client.set(
                redis_key, 
                self._serialize_to_json(stage),
                ex=REDIS_TTL
            )
            
            # Also add to customer's stage list
            cust_stages_key = f"customer:{stage.customer_id}:stages"
            redis_client.sadd(cust_stages_key, stage.stage_id)
            redis_client.expire(cust_stages_key, REDIS_TTL)
            
            return True
            
        except Exception as e:
            print(f"Error saving customer stage: {e}")
            return False
    
    def get_customer_stage(self, customer_id: str, stage_id: str) -> Optional[customer_stage_metadata]:
        """
        Get a specific stage for a customer
        
        Args:
            customer_id: Customer ID
            stage_id: Stage ID
            
        Returns:
            Optional[customer_stage_metadata]: Stage object if found, None otherwise
        """
        try:
            # Try to get from Redis first
            redis_key = f"customer:{customer_id}:stage:{stage_id}"
            cached_stage = redis_client.get(redis_key)
            
            if cached_stage:
                # Stage found in cache
                return self._deserialize_from_json(cached_stage, customer_stage_metadata)
            
            # Not in cache, get from DynamoDB
            cust_pk = f"CUST#{customer_id}"
            stage_sk = f"STAGE#{stage_id}"
            
            response = table.get_item(Key={'PK': cust_pk, 'SK': stage_sk})
            
            if 'Item' in response:
                # Create stage object from DynamoDB item
                item = response['Item']
                stage = customer_stage_metadata()
                stage.customer_id = item.get('customerId')
                stage.stage_id = item.get('stageId')
                stage.stage_name = item.get('stageName')
                stage.stage_created_at = item.get('createdAt')
                stage.stage_updated_at = item.get('updatedAt')
                stage.is_deleted = item.get('isDeleted', False)
                stage.stage_data = item.get('stageData', {})
                
                # Cache in Redis for future requests
                redis_client.set(
                    redis_key, 
                    self._serialize_to_json(stage),
                    ex=REDIS_TTL
                )
                
                # Also add to customer's stage list
                cust_stages_key = f"customer:{customer_id}:stages"
                redis_client.sadd(cust_stages_key, stage_id)
                redis_client.expire(cust_stages_key, REDIS_TTL)
                
                return stage
            
            return None
            
        except Exception as e:
            print(f"Error getting customer stage: {e}")
            return None
    
    def get_all_customer_stages(self, customer_id: str) -> List[customer_stage_metadata]:
        """
        Get all stages for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List[customer_stage_metadata]: List of stage objects
        """
        try:
            stages = []
            
            # Try to get stage IDs from Redis first
            cust_stages_key = f"customer:{customer_id}:stages"
            cached_stage_ids = redis_client.smembers(cust_stages_key)
            
            if cached_stage_ids:
                # Get each stage from cache or DB
                for stage_id in cached_stage_ids:
                    stage = self.get_customer_stage(customer_id, stage_id)
                    if stage and not stage.is_deleted:
                        stages.append(stage)
                return stages
            
            # Not in cache, query DynamoDB
            cust_pk = f"CUST#{customer_id}"
            response = table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": cust_pk,
                    ":sk_prefix": "STAGE#"
                }
            )
            
            # Process results
            for item in response.get('Items', []):
                stage_id = item.get('stageId')
                if stage_id:
                    # Add to Redis set for future lookups
                    redis_client.sadd(cust_stages_key, stage_id)
                    
                    # Create stage object
                    stage = customer_stage_metadata()
                    stage.customer_id = item.get('customerId')
                    stage.stage_id = item.get('stageId')
                    stage.stage_name = item.get('stageName')
                    stage.stage_created_at = item.get('createdAt')
                    stage.stage_updated_at = item.get('updatedAt')
                    stage.is_deleted = item.get('isDeleted', False)
                    stage.stage_data = item.get('stageData', {})
                    
                    # Cache individual stage
                    redis_key = f"customer:{customer_id}:stage:{stage_id}"
                    redis_client.set(
                        redis_key, 
                        self._serialize_to_json(stage),
                        ex=REDIS_TTL
                    )
                    
                    if not stage.is_deleted:
                        stages.append(stage)
            
            # Set expiry on the Redis set
            if stages:
                redis_client.expire(cust_stages_key, REDIS_TTL)
                
            return stages
            
        except Exception as e:
            print(f"Error getting customer stages: {e}")
            return []
    
    def update_customer_stage(self, stage: customer_stage_metadata) -> bool:
        """
        Update customer stage data
        
        Args:
            stage: Customer stage metadata object with updated fields
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check required fields
            if not hasattr(stage, 'customer_id') or not stage.customer_id:
                print("Cannot update stage: No customer_id provided")
                return False
                
            if not hasattr(stage, 'stage_id') or not stage.stage_id:
                print("Cannot update stage: No stage_id provided")
                return False
            
            # Get existing stage to preserve fields not in the update
            existing_stage = self.get_customer_stage(stage.customer_id, stage.stage_id)
            if not existing_stage:
                print(f"Cannot update stage: Stage {stage.stage_id} for customer {stage.customer_id} not found")
                return False
            
            # Update timestamp
            stage.stage_updated_at = self._generate_timestamp()
            
            # Merge existing and new data
            for attr in dir(stage):
                if not attr.startswith('__') and hasattr(stage, attr):
                    value = getattr(stage, attr)
                    if value is not None:
                        setattr(existing_stage, attr, value)
            
            # Save the updated stage
            return self.save_customer_stage(existing_stage)
            
        except Exception as e:
            print(f"Error updating customer stage: {e}")
            return False
