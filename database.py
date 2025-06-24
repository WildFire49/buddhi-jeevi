from typing import Dict, Any, Optional

def get_mock_vector_db():
    """Mocks a Vector DB containing our 'smart action' documents."""
    
    return [
        {
            "action_id": "JLG_S0_A1_LOGIN",
            "stage_name": "Authentication",
            "description_for_llm": "This is the initial step for a field officer to log in to the system. It requires the employee ID and password.",
            "action_type": "USER_DATA_COLLECTION",
            "api_endpoint_ref": "Login",
            "ui_definition": {
                "step_title": "Officer Login",
                "step_description": "Please enter your credentials to begin.",
                "bot_message": "Welcome. Please log in to continue.",
                "form_fields": [
                    {
                        "field_id": "employeeId",
                        "component_type": "Text Input Field",
                        "properties": {
                            "label": "Employee ID",
                            "hint": "Enter your unique employee ID",
                            "input_type": "text",
                            "required": True
                        }
                    },
                    {
                        "field_id": "password",
                        "component_type": "Password Field",
                        "properties": {
                            "label": "Password",
                            "hint": "Enter your password",
                            "input_type": "password",
                            "required": True
                        }
                    }
                ],
                "submit_button": {
                    "text": "Login",
                    "enabled_when_valid": True
                }
            },
            "api_call_details": {
                "http_method": "POST",
                "endpoint_path": "/api/v1/auth/login",
                "request_payload_template": {
                    "employeeId": "string",
                    "password": "string",
                    "deviceUniqueNo": "string"
                }
            }
        },
        {
            "action_id": "JLG_S0_A3_MARK_ATTENDANCE_API",
            "stage_name": "Attendance",
            "description_for_llm": "This is an automatic backend action to mark the officer's attendance by capturing their current geolocation after a successful login.",
            "action_type": "API_EXECUTION",
            "api_endpoint_ref": "Attendance Marking",
            "api_call_details": {
                "http_method": "POST",
                "endpoint_path": "/api/v1/attendance/mark",
                "request_payload_template": {
                    "employeeId": "string",
                    "latitude": "float",
                    "longitude": "float",
                    "eventType": "string"
                }
            }
        },
        {
            "action_id": "JLG_S1_A1_CAPTURE_AADHAAR",
            "stage_name": "EKYC & ID Generation",
            "description_for_llm": "This step involves onboarding capturing the customer's Aadhar number and a unique AUA token to perform EKYC and generate a new customer ID in the system.",
            "action_type": "USER_DATA_COLLECTION",
            "api_endpoint_ref": "Generate Customer ID",
            "ui_definition": {
                "step_title": "Aadhar Verification",
                "step_description": "Please provide the customer's Aadhar details for KYC.",
                "bot_message": "Let's begin onboarding a new customer. Please enter their 12-digit Aadhar number and the UID token.",
                "form_fields": [
                    {
                        "field_id": "aadharNumber",
                        "component_type": "Number Input Field",
                        "properties": {
                            "label": "Aadhar Number",
                            "hint": "Enter the 12-digit Aadhar number",
                            "input_type": "number",
                            "required": True,
                            "validation_pattern": "^[2-9]\\d{11}$",
                            "validation_message": "Please enter a valid 12-digit Aadhar number"
                        }
                    },
                    {
                        "field_id": "auaSpecificUidToken",
                        "component_type": "Text Input Field",
                        "properties": {
                            "label": "UID Token",
                            "hint": "Enter the UID token for KYC",
                            "input_type": "text",
                            "required": True
                        }
                    }
                ],
                "submit_button": {
                    "text": "Generate Customer ID",
                    "enabled_when_valid": True
                }
            },
            "api_call_details": None
        },
        {
            "action_id": "JLG_S1_A2_GENERATE_CUSTOMER_ID_API",
            "stage_name": "EKYC & ID Generation",
            "description_for_llm": "This is a backend action that sends the Aadhar and UID token to the server to generate a customer ID.",
            "action_type": "API_EXECUTION",
            "api_endpoint_ref": "Generate Customer ID",
            "api_call_details": {
                "http_method": "POST",
                "endpoint_path": "/api/v1/customer/generate-id",
                "request_payload_template": {
                    "transactionId": "string",
                    "aadharNumber": "string",
                    "auaSpecificUidToken": "string"
                }
            }
        },
        {
            "action_id": "JLG_S1_A3_CAPTURE_MOBILE_OTP",
            "stage_name": "EKYC & ID Generation",
            "description_for_llm": "This step validates the customer's mobile number by sending and verifying an OTP.",
            "action_type": "USER_DATA_COLLECTION",
            "api_endpoint_ref": "Generate Mobile Validation OTP",
            "ui_definition": {
                "step_title": "Mobile Verification",
                "step_description": "Please verify the customer's mobile number.",
                "bot_message": "Great. Now, let's verify the customer's mobile number. Please enter it below to receive an OTP.",
                "form_fields": [
                    {
                        "field_id": "mobileNumber",
                        "component_type": "Number Input Field",
                        "properties": {
                            "label": "Mobile Number",
                            "hint": "Enter 10-digit mobile number",
                            "input_type": "number",
                            "required": True,
                            "validation_pattern": "^[6-9]\\d{9}$",
                            "validation_message": "Please enter a valid 10-digit mobile number"
                        }
                    }
                ],
                "submit_button": {
                    "text": "Send OTP",
                    "enabled_when_valid": True
                }
            },
            "api_call_details": None
        },
        {
            "action_id": "JLG_S1_A4_SUBMIT_L1_DETAILS_API",
            "stage_name": "EKYC & ID Generation",
            "description_for_llm": "This backend action submits all collected L1 details including demographics and customer photo for initial approval.",
            "action_type": "API_EXECUTION",
            "api_endpoint_ref": "Submit L1 Additional Details",
            "api_call_details": {
                "http_method": "POST",
                "endpoint_path": "/api/v1/customer/l1/submit",
                "request_payload_template": {
                    "custId": "string",
                    "demographics": "object",
                    "documents": "object"
                }
            }
        },
        {
            "action_id": "JLG_S2_A1_CAPTURE_HOUSEHOLD_MEMBER",
            "stage_name": "Household & Financial Details",
            "description_for_llm": "This step captures the details of a household member, including their relationship and if they are a nominee.",
            "action_type": "USER_DATA_COLLECTION",
            "api_endpoint_ref": "Submit/Update Household Member Details",
            "ui_definition": {
                "step_title": "Household Member Details",
                "step_description": "Add a household member's information.",
                "bot_message": "Now, let's add the details for each household member. Please start with the first person.",
                "form_fields": [
                    {
                        "field_id": "fullName",
                        "component_type": "Text Input Field",
                        "properties": {
                            "label": "Full Name",
                            "hint": "Enter member's full name",
                            "required": True
                        }
                    },
                    {
                        "field_id": "relationship",
                        "component_type": "Text Input Field",
                        "properties": {
                            "label": "Relationship",
                            "hint": "e.g., Spouse, Son, Father",
                            "required": True
                        }
                    },
                    {
                        "field_id": "dob",
                        "component_type": "Date Picker",
                        "properties": {
                            "label": "Date of Birth",
                            "required": True
                        }
                    },
                    {
                        "field_id": "isNominee",
                        "component_type": "Checkbox",
                        "properties": {
                            "label": "Set as Nominee",
                            "required": False
                        }
                    }
                ],
                "submit_button": {
                    "text": "Save Member",
                    "enabled_when_valid": True
                }
            },
            "api_call_details": None
        },
        {
            "action_id": "JLG_S2_A2_ELIGIBILITY_CHECK_API",
            "stage_name": "Household & Financial Details",
            "description_for_llm": "This backend action performs an eligibility check based on the customer's submitted financial details.",
            "action_type": "API_EXECUTION",
            "api_endpoint_ref": "Eligibility Check",
            "api_call_details": {
                "http_method": "POST",
                "endpoint_path": "/api/v1/loan/eligibility-check",
                "request_payload_template": {
                    "custId": "string",
                    "annualCustomerIncome": "number",
                    "monthlyLiabilities": "number"
                }
            }
        },
        {
            "action_id": "JLG_S3_A1_CAPTURE_IFSC",
            "stage_name": "Bank Account Details",
            "description_for_llm": "This step captures the customer's bank IFSC code to fetch branch details automatically.",
            "action_type": "USER_DATA_COLLECTION",
            "api_endpoint_ref": "Get Bank Details from IFSC",
            "ui_definition": {
                "step_title": "Bank Details",
                "step_description": "Let's find the bank branch using the IFSC code.",
                "bot_message": "We're almost done! Please enter the bank's IFSC code to fetch the branch details.",
                "form_fields": [
                    {
                        "field_id": "ifsc",
                        "component_type": "Text Input Field",
                        "properties": {
                            "label": "IFSC Code",
                            "hint": "Enter the 11-character IFSC code",
                            "input_type": "text",
                            "required": True,
                            "validation_pattern": "^[A-Z]{4}0[A-Z0-9]{6}$",
                            "validation_message": "Please enter a valid IFSC code"
                        }
                    }
                ],
                "submit_button": {
                    "text": "Find Branch",
                    "enabled_when_valid": True
                }
            },
            "api_call_details": None
        },
        {
            "action_id": "JLG_S3_A2_GET_BANK_DETAILS_API",
            "stage_name": "Bank Account Details",
            "description_for_llm": "This backend action fetches bank branch details using the provided IFSC code.",
            "action_type": "API_EXECUTION",
            "api_endpoint_ref": "Get Bank Details from IFSC",
            "api_call_details": {
                "http_method": "GET",
                "endpoint_path": "/api/v1/bank/details-from-ifsc",
                "request_payload_template": {
                    "ifsc": "string"
                }
            }
        },
        {
            "action_id": "JLG_S3_A3_CAPTURE_BANK_ACCOUNT",
            "stage_name": "Bank Account Details",
            "description_for_llm": "This final data collection step captures the remaining bank account details and proof of account.",
            "action_type": "USER_DATA_COLLECTION",
            "api_endpoint_ref": "Submit Bank Details (L3)",
            "ui_definition": {
                "step_title": "Account Confirmation",
                "step_description": "Please confirm the account details and upload proof.",
                "bot_message": "Perfect. The branch is [branchName]. Now, please provide the account holder's name and account number.",
                "form_fields": [
                    {
                        "field_id": "accountHolderName",
                        "component_type": "Text Input Field",
                        "properties": {
                            "label": "Account Holder Name",
                            "hint": "Name as per bank records",
                            "required": True
                        }
                    },
                    {
                        "field_id": "accountNumber",
                        "component_type": "Number Input Field",
                        "properties": {
                            "label": "Account Number",
                            "hint": "Enter the full bank account number",
                            "input_type": "number",
                            "required": True
                        }
                    },
                    {
                        "field_id": "proofOfAccount",
                        "component_type": "File Upload",
                        "properties": {
                            "label": "Upload Bank Proof",
                            "hint": "e.g., Photo of passbook or cancelled cheque",
                            "required": True
                        }
                    },
                    {
                        "field_id": "consent",
                        "component_type": "Checkbox",
                        "properties": {
                            "label": "I confirm all details are correct and consent to the terms.",
                            "required": True
                        }
                    }
                ],
                "submit_button": {
                    "text": "Complete Onboarding",
                    "enabled_when_valid": True
                }
            },
            "api_call_details": None
        },
        {
            "action_id": "JLG_S3_A4_SUBMIT_BANK_DETAILS_API",
            "stage_name": "Bank Account Details",
            "description_for_llm": "This is the final backend action to submit all L3 bank details and complete the customer onboarding flow.",
            "action_type": "API_EXECUTION",
            "api_endpoint_ref": "Submit Bank Details (L3)",
            "api_call_details": {
                "http_method": "POST",
                "endpoint_path": "/api/v1/customer/l3/submit",
                "request_payload_template": {
                    "custId": "string",
                    "accountHolderName": "string",
                    "accountNumber": "string",
                    "ifsc": "string",
                    "documents": "object"
                }
            }
        }
    ]

def get_action_by_id(action_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single action document by its action_id from the mock database.
    """
    for action in get_mock_vector_db():
        if action.get("action_id") == action_id:
            return action
    return None