import boto3
from boto3.dynamodb.conditions import Key
import uuid
from datetime import datetime, timezone
import pprint
import bcrypt # For password hashing
import secrets # For generating access tokens

# --- Configuration ---
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'OnboardingSystem'
MOBILE_INDEX_NAME = 'MobileNumberIndex' # The name of our new GSI
table = dynamodb.Table(TABLE_NAME)

# --- NEW: User Authentication Functions ---

def register_user(user_id, user_name, password):
    """
    Registers a new user by storing a secure hash of their password.
    """
    print(f"--- Registering User: {user_name} ({user_id}) ---")
    user_pk = f"USER#{user_id}"

    # Generate a salt and hash the password
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    try:
        table.put_item(
            Item={
                'PK': user_pk,
                'SK': 'METADATA',
                'userId': user_id,
                'userName': user_name,
                'passwordHash': password_hash,
                'createdAt': datetime.now(timezone.utc).isoformat()
            },
            ConditionExpression='attribute_not_exists(PK)'
        )
        print(f"✅ User '{user_name}' registered successfully.")
        return True
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        print(f"❌ Error: User ID '{user_id}' already exists.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

def login_user(user_id):
    """
    Logs a user in by checking their password against the stored hash.
    If successful, generates and stores a new access token.
    """
    print(f"\n--- Attempting login for User ID: {user_id} ---")
    user_pk = f"USER#{user_id}"

    # Get the user's stored metadata
    user_data = table.get_item(Key={'PK': user_pk, 'SK': 'METADATA'}).get('Item')

    if not user_data or 'passwordHash' not in user_data:
        print("❌ Login failed: User not found.")
        return None

    stored_hash_bytes = user_data['passwordHash'].encode('utf-8')

    # Check the provided password against the stored hash
    if bcrypt.checkpw(password_bytes, stored_hash_bytes):
        print("✅ Login successful. Generating access token.")
        # Generate a new secure access token
        access_token = secrets.token_hex(16)
        
        # Update the user's record with the new token
        table.update_item(
            Key={'PK': user_pk, 'SK': 'METADATA'},
            UpdateExpression="SET accessToken = :token",
            ExpressionAttributeValues={":token": access_token}
        )
        return access_token
    else:
        print("❌ Login failed: Invalid password.")
        return None

# --- MODIFIED: Onboarding Function ---

def onboard_customer(user_id, customer_name, customer_email, customer_mobile):
    """
    MODIFIED: Now includes the customer's mobile number.
    """
    customer_id = f"cust_{uuid.uuid4()}"
    user_pk = f"USER#{user_id}"
    cust_pk = f"CUST#{customer_id}"
    onboarded_at = datetime.now(timezone.utc).isoformat()

    print(f"\n--- Onboarding Customer: {customer_name} for User ID: {user_id} ---")

    initial_stages = {"ekyc": "pending", "nominee_details": "pending"} # Shortened for brevity

    try:
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {'Put': {'TableName': TABLE_NAME, 'Item': {
                            'PK': cust_pk, 'SK': 'METADATA', 'customerId': customer_id,
                            'customerName': customer_name, 'customerEmail': customer_email,
                            'mobileNumber': customer_mobile, # <-- ADDED MOBILE NUMBER
                            'onboardedBy': user_pk, 'onboardedAt': onboarded_at,
                            'currentState': 'ekyc', 'stages': initial_stages},
                         'ConditionExpression': 'attribute_not_exists(PK)'}},
                {'Put': {'TableName': TABLE_NAME, 'Item': {
                            'PK': user_pk, 'SK': cust_pk, 'customerName': customer_name,
                            'customerId': customer_id, 'onboardedAt': onboarded_at},
                         'ConditionExpression': 'attribute_not_exists(PK)'}}
            ]
        )
        print("✅ Customer onboarded successfully.")
        return customer_id
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return None

# --- NEW: Customer Lookup Function ---

def get_customer_by_mobile(mobile_number):
    """
    Finds a customer using their mobile number by querying the GSI.
    """
    print(f"\n--- Searching for customer with Mobile: {mobile_number} ---")
    try:
        response = table.query(
            IndexName=MOBILE_INDEX_NAME,
            KeyConditionExpression=Key('mobileNumber').eq(mobile_number)
        )
        items = response.get('Items', [])
        if not items:
            print("⚠️ No customer found with that mobile number.")
            return None
        # In a well-designed system, mobile number should be unique.
        # We return the first match.
        print(f"✅ Found customer: {items[0]['customerName']}")
        return items[0]
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return None

# --- UNCHANGED: Helper Functions (get_customer_profile, etc.) ---
# (Include the other functions from the previous response here for a complete script)
def get_customer_profile(customer_id):
    cust_pk = f"CUST#{customer_id}"
    print(f"\n--- Getting profile for Customer ID: {customer_id} ---")
    response = table.get_item(Key={'PK': cust_pk, 'SK': 'METADATA'})
    return response.get('Item')

# --- Main Execution Block (Example Usage) ---

if __name__ == "__main__":
    # 1. Register a new user
    register_user(
        user_id="sanjay_s",
        user_name="Sanjay Singh",
        password="SicherePassword!123"
    )

    # 2. Login with the new user credentials
    token = login_user(user_id="sanjay_s", password="SicherePassword!123")
    if token:
        print(f"Received Access Token: {token}")

    # 3. Onboard a customer with a mobile number
    new_cust_id = onboard_customer(
        user_id="sanjay_s",
        customer_name="Priya Das",
        customer_email="priya.das@example.com",
        customer_mobile="+919998887776"
    )

    if new_cust_id:
        # 4. Now, find that customer using their mobile number
        found_customer = get_customer_by_mobile("+919998887776")
        if found_customer:
            print("\n--- Customer Details Found via Mobile ---")
            pprint.pprint(found_customer)