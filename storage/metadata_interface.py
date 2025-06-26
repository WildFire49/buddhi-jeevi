class user_metadata:
    user_id: str
    user_name: str
    user_email: str
    user_mobile: str
    user_password: str
    user_created_at: str
    
class customer_metadata:
    mobile_number: str
    customer_name: str
    customer_created_at: str
    customer_updated_at: str
    customer_id: str
    is_deleted: bool

class user_customer_metadata:
    user_id: str
    customer_id: str
    user_customer_created_at: str
    user_customer_updated_at: str
    user_customer_id: str
    is_deleted: bool

class customer_stage_metadata:
    stage_id: str
    customer_id: str
    stage_name: str
    stage_created_at: str
    stage_updated_at: str
    is_deleted: bool
    stage_data: dict
