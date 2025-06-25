import os
import json
import chromadb
from langchain_openai import OpenAIEmbeddings # New import for OpenAI embeddings

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define workflow steps
workflow_steps = {
    "mobile_otp_generation": {
        "step_id": "mobile_otp_generation",
        "step_title": "Mobile OTP Generation",
        "step_description": "Enter client's mobile to generate OTP for identity verification",
        "messages": [
            {
                "id": "msg_3",
                "type": "bot_message",
                "content": "Let's start with verifying your mobile number. Please enter your mobile number to receive an OTP."
            }
        ],
        "ui_components": [
            {
                "component_type": "text_input",
                "properties": {
                    "label": "Mobile Number",
                    "hint": "+91 XXXXX XXXXX",
                    "input_type": "phone",
                    "max_length": 10
                }
            },
            {
                "component_type": "button",
                "properties": {
                    "text": "Generate OTP",
                    "enabled": True,
                    "action": "generate_otp"
                }
            }
        ],
        "validation": {
            "required": True,
            "validation_type": "mobile_format"
        },
        "next_action": {
            "endpoint": "/api/main/customer/{mobile}/generateOTP",
            "method": "GET",
            "params": {
                "type": "ONBOARDING"
            }
        }
    },
    "mobile_otp_validation": {
        "step_id": "mobile_otp_validation",
        "step_title": "Mobile OTP Validation",
        "step_description": "Validate client ownership of provided mobile number",
        "messages": [
            {
                "id": "msg_4",
                "type": "bot_message",
                "content": "Please enter the OTP sent to your mobile number."
            }
        ],
        "ui_components": [
            {
                "component_type": "otp_input",
                "properties": {
                    "label": "Enter OTP",
                    "length": 6,
                    "input_type": "number"
                }
            },
            {
                "component_type": "button",
                "properties": {
                    "text": "Verify OTP",
                    "enabled": True,
                    "action": "validate_otp"
                }
            }
        ],
        "validation": {
            "required": True,
            "validation_type": "otp_format"
        },
        "next_action": {
            "endpoint": "/api/main/customer/validateOTP",
            "method": "POST",
            "params": {
                "session_id": "placeholder"
            }
        }
    },
    "aadhar_biometric": {
        "step_id": "aadhar_biometric",
        "step_title": "Aadhaar & Biometric",
        "step_description": "Complete mandatory KYC for customer onboarding with Aadhaar and biometric verification",
        "messages": [
            {
                "id": "msg_6",
                "type": "bot_message",
                "content": "Now we'll complete your KYC verification using Aadhaar and biometric scan."
            }
        ],
        "ui_components": [
            {
                "component_type": "text_input",
                "properties": {
                    "label": "Aadhaar Number",
                    "hint": "XXXX XXXX XXXX",
                    "input_type": "number",
                    "max_length": 12
                }
            },
            {
                "component_type": "biometric_scanner",
                "properties": {
                    "scan_type": "fingerprint",
                    "instruction": "Place finger on scanner"
                }
            }
        ],
        "validation": {
            "required": True,
            "validation_type": "ekyc_complete"
        },
        "next_action": {
            "endpoint": "/api/main/customer/generate",
            "method": "GET",
            "params": {
                "session_id": "placeholder"
            }
        }
    }
}

# Define action to step mapping
action_to_step = {
    "JLG_S1_A3_CAPTURE_MOBILE_OTP": "mobile_otp_generation",
    "JLG_S1_A3_VALIDATE_OTP": "mobile_otp_validation",
    "JLG_S1_A1_CAPTURE_AADHAAR": "aadhar_biometric"
}

# Define the onboarding flow overview
onboarding_flow = {
    "step_id": "onboarding_flow",
    "step_title": "Onboarding Process",
    "step_description": "Complete onboarding flow for microfinance clients",
    "workflow_steps": [
        {"step": "1", "name": "Video Consent", "description": "Watch consent video and provide agreement"},
        {"step": "2", "name": "Mobile OTP Generation", "description": "Enter mobile number to receive OTP"},
        {"step": "3", "name": "Mobile OTP Validation", "description": "Validate mobile number with OTP"},
        {"step": "4", "name": "Pincode Entry", "description": "Enter pincode to validate geographical eligibility"},
        {"step": "5", "name": "Aadhaar & Biometric", "description": "Complete KYC verification with Aadhaar and biometric"},
        {"step": "6", "name": "Photo & KYC Documents", "description": "Capture photo and upload KYC documents"},
        {"step": "7", "name": "Household Members Entry", "description": "Capture household members and their KYC details"},
        {"step": "8", "name": "Income & Loan Preference", "description": "Submit income details and loan preferences"},
        {"step": "9", "name": "Loan Eligibility Calculation", "description": "System calculates loan eligibility"},
        {"step": "10", "name": "Bank Account Details", "description": "Enter bank account details for verification"},
        {"step": "11", "name": "Group Creation", "description": "Form lending groups and assign Group Head"},
        {"step": "12", "name": "Onboarding Complete", "description": "Group created successfully, process completed"}
    ]
}

def upload_workflow_to_chroma():
    """Upload workflow steps to ChromaDB collection"""
    try:
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host='3.6.132.24', port=8000)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        # Initialize HuggingFace embeddings with Llama 3 model
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="nomic-embed-text")

        
        # Check if collection exists, if not create it
        try:
            collection = client.get_collection("onboarding_flow")
            print("Collection 'onboarding_flow' already exists")
        except Exception:
            collection = client.create_collection(
                name="onboarding_flow",
                metadata={"hnsw:space": "cosine"}
            )
            print("Created new collection 'onboarding_flow'")
        
        # Prepare documents for each workflow step
        documents = []
        metadatas = []
        ids = []
        
        # Add workflow steps
        for step_id, step_data in workflow_steps.items():
            # Create a document with step details
            doc_text = f"{step_id}: {step_data['step_title']} - {step_data['step_description']}"
            documents.append(doc_text)
            
            # Store the full step data in metadata
            metadatas.append({
                "action_id": step_id,
                "description": step_data['step_description'],
                "full_action": json.dumps(step_data)
            })
            
            ids.append(f"workflow_step_{step_id}")
        
        # Add action to step mappings
        for action_id, step_id in action_to_step.items():
            step_data = workflow_steps[step_id]
            doc_text = f"{action_id}: Maps to {step_id} - {step_data['step_title']}"
            documents.append(doc_text)
            
            metadatas.append({
                "action_id": action_id,
                "description": f"Maps to {step_id}",
                "step_id": step_id,
                "full_action": json.dumps(step_data)
            })
            
            ids.append(f"action_mapping_{action_id}")
        
        # Add the onboarding flow overview
        doc_text = f"onboarding_flow: {onboarding_flow['step_title']} - {onboarding_flow['step_description']}"
        documents.append(doc_text)
        
        metadatas.append({
            "action_id": "onboarding_flow",
            "description": onboarding_flow['step_description'],
            "full_action": json.dumps(onboarding_flow)
        })
        
        ids.append("workflow_overview")
        
        # Generate embeddings for each document
        embeddings_list = []
        for doc in documents:
            embedding = embeddings.embed_query(doc)
            embeddings_list.append(embedding)
        
        # Add documents to collection
        collection.add(
            embeddings=embeddings_list,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Successfully added {len(documents)} workflow items to ChromaDB collection 'onboarding_flow'")
        
    except Exception as e:
        print(f"Error uploading workflow to ChromaDB: {e}")

if __name__ == "__main__":
    upload_workflow_to_chroma()
