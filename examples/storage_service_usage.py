"""
Example usage of the StorageService class for metadata storage
"""
import os
import sys
import uuid
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.storage_service import StorageService
from storage.metadata_interface import user_metadata, customer_metadata, user_customer_metadata, customer_stage_metadata

def main():
    """Demonstrate usage of StorageService with all metadata types"""
    # Initialize the storage service
    storage = StorageService()
    
    # ===== User Operations =====
    print("\n=== User Operations ===")
    
    # Create a new user
    user = user_metadata()
    user.user_name = "John Doe"
    user.user_email = "john.doe@example.com"
    # In a real application, you would hash the password before saving
    user.user_password_hash = "hashed_password_here"
    
    # Save the user
    if storage.save_user(user):
        print(f"User saved successfully with ID: {user.user_id}")
    else:
        print("Failed to save user")
        return
    
    # Retrieve user by ID
    retrieved_user = storage.get_user_by_id(user.user_id)
    if retrieved_user:
        print(f"Retrieved user by ID: {retrieved_user.user_name}")
    
    # Retrieve user by email
    retrieved_user = storage.get_user_by_email(user.user_email)
    if retrieved_user:
        print(f"Retrieved user by email: {retrieved_user.user_name}")
    
    # ===== Customer Operations =====
    print("\n=== Customer Operations ===")
    
    # Create a new customer
    customer = customer_metadata()
    customer.customer_name = "ACME Corporation"
    customer.mobile_number = "1234567890"
    
    # Save the customer
    if storage.save_customer(customer):
        print(f"Customer saved successfully with ID: {customer.customer_id}")
    else:
        print("Failed to save customer")
        return
    
    # Retrieve customer by ID
    retrieved_customer = storage.get_customer_by_id(customer.customer_id)
    if retrieved_customer:
        print(f"Retrieved customer by ID: {retrieved_customer.customer_name}")
    
    # Retrieve customer by mobile number
    retrieved_customer = storage.get_customer_by_mobile(customer.mobile_number)
    if retrieved_customer:
        print(f"Retrieved customer by mobile: {retrieved_customer.customer_name}")
    
    # Update customer information
    customer.customer_name = "ACME Corporation Updated"
    if storage.update_customer(customer):
        print(f"Customer updated successfully: {customer.customer_name}")
    
    # ===== User-Customer Relationship Operations =====
    print("\n=== User-Customer Relationship Operations ===")
    
    # Create a relationship between user and customer
    relation = user_customer_metadata()
    relation.user_id = user.user_id
    relation.customer_id = customer.customer_id
    
    # Save the relationship
    if storage.save_user_customer_relation(relation):
        print(f"User-Customer relationship saved with ID: {relation.user_customer_id}")
    else:
        print("Failed to save relationship")
    
    # Get all customers for a user
    user_customers = storage.get_user_customers(user.user_id)
    print(f"User has {len(user_customers)} customers:")
    for cust in user_customers:
        print(f"- {cust.customer_name}")
    
    # Get all users for a customer
    customer_users = storage.get_customer_users(customer.customer_id)
    print(f"Customer has {len(customer_users)} users:")
    for usr in customer_users:
        print(f"- {usr.user_name}")
    
    # ===== Customer Stage Operations =====
    print("\n=== Customer Stage Operations ===")
    
    # Create a new customer stage
    stage = customer_stage_metadata()
    stage.customer_id = customer.customer_id
    stage.stage_id = str(uuid.uuid4())
    stage.stage_name = "Onboarding"
    stage.stage_data = {
        "progress": 50,
        "completed_steps": ["intro", "profile"],
        "pending_steps": ["verification", "payment"],
        "notes": "Customer is in the onboarding process"
    }
    
    # Save the stage
    if storage.save_customer_stage(stage):
        print(f"Customer stage saved with ID: {stage.stage_id}")
    else:
        print("Failed to save customer stage")
    
    # Retrieve a specific stage
    retrieved_stage = storage.get_customer_stage(customer.customer_id, stage.stage_id)
    if retrieved_stage:
        print(f"Retrieved stage: {retrieved_stage.stage_name}")
        print(f"Stage data: {retrieved_stage.stage_data}")
    
    # Create another stage
    stage2 = customer_stage_metadata()
    stage2.customer_id = customer.customer_id
    stage2.stage_id = str(uuid.uuid4())
    stage2.stage_name = "Active"
    stage2.stage_data = {
        "active_since": datetime.now().isoformat(),
        "subscription_tier": "premium"
    }
    storage.save_customer_stage(stage2)
    
    # Get all stages for a customer
    all_stages = storage.get_all_customer_stages(customer.customer_id)
    print(f"Customer has {len(all_stages)} stages:")
    for stg in all_stages:
        print(f"- {stg.stage_name}")
    
    # Update a stage
    stage.stage_data["progress"] = 75
    stage.stage_data["completed_steps"].append("verification")
    if storage.update_customer_stage(stage):
        print(f"Stage updated successfully. New progress: {stage.stage_data['progress']}%")
    
    # ===== Cleanup (optional) =====
    print("\n=== Cleanup Operations ===")
    
    # Soft delete a customer (mark as deleted)
    if storage.delete_customer(customer.customer_id, hard_delete=False):
        print(f"Customer soft-deleted: {customer.customer_id}")
    
    # Delete a user (hard delete)
    if storage.delete_user(user.user_id):
        print(f"User deleted: {user.user_id}")

if __name__ == "__main__":
    main()
