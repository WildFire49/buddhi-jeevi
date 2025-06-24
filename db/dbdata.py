def getObjects():
    return   [
        {
            "action_id": "onboarding-step-001",
            "stage_name": "EKYC & ID Generation",
            "description_for_llm": "Onboard customer, Onboard customer, Onboard customer, Onboard new customer,Collect user's PAN and Aadhaar number for identity verification.",
            "action_type": "USER_ONBOARDING",
            "preconditions": ["user_is_logged_in"],
            "next_action_id_success": "onboarding-step-002",
            "next_action_id_failure": "onboarding-step-001",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "mobile_number",
                        "component_type": "text_input",
                        "properties": {
                            "label": "PAN Number",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid mobile format"
                        }
                    },
                    {
                        "field_id": "adhaar_number",
                        "component_type": "text_input",
                        "properties": {
                            "label": "PAN Number",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid AADHAAR format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/verify-id",
                    "request_payload_template": {
                        "pan": "{{pan_number}}",
                        "aadhaar": "{{aadhaar_number}}"
                    }
                }
            ]
        },
        {
            "action_id": "onboarding-step-002",
            "stage_name": "Customer basic details",
            "description_for_llm": "add customer basic details, add customer basic details, add customer basic details, add new customer basic details",
            "action_type": "USER_BASIC_DEtAILS",
            "preconditions": ["user_is_logged_in", "user must be verified"],
            "next_action_id_success": "onboarding-step-003",
            "next_action_id_failure": "onboarding-step-002",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "first_name",
                        "component_type": "text_input",
                        "properties": {
                            "label": "First Name",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid first format"
                        }
                    },
                    {
                        "field_id": "second_name",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Second Name",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid second name format"
                        }
                    },
                    {
                        "field_id": "pincode",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Pincode",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid pincode format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/basic-details",
                    "request_payload_template": {
                        "pan": "{{first_name}}",
                        "aadhaar": "{{second_name}}",
                        "pincode": "{{pincode}}"
                    }
                }
            ]
        },

        {
            "action_id": "onboarding-step-003",
            "stage_name": "Customer nomniee details",
            "description_for_llm": "customer nomniee details",
            "action_type": "USER_BASIC_DEtAILS",
            "preconditions": ["user_is_logged_in"],
            "next_action_id_success": "onboarding-step-004",
            "next_action_id_failure": "onboarding-step-003",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "nominee_first_name",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Nominee First Name",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid nominee first format"
                        }
                    },
                    {
                        "field_id": "nominee_second_name",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Nominee Second Name",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid nominee second name format"
                        }
                    },
                    {
                        "field_id": "relationship",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Pincode",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid pincode format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/nominee-details",
                    "request_payload_template": {
                        "pan": "{{first_name}}",
                        "aadhaar": "{{second_name}}",
                        "pincode": "{{pincode}}"
                    }
                }
            ]
        },
        {
            "action_id": "onboarding-step-004",
            "stage_name": "Customer income details",
            "description_for_llm": "customer income details, customer earning details",
            "action_type": "USER_INCOME_DEtAILS",
            "preconditions": ["user_is_logged_in"],
            "next_action_id_success": "onboarding-step-005",
            "next_action_id_failure": "onboarding-step-004",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "income_type",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Income type",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid income type format"
                        }
                    },
                    {
                        "field_id": "amount",
                        "component_type": "text_input",
                        "properties": {
                            "label": "amount",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid amount format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/nominee-details",
                    "request_payload_template": {
                        "pan": "{{first_name}}",
                        "aadhaar": "{{second_name}}",
                        "pincode": "{{pincode}}"
                    }
                }
            ]
        },
        {
            "action_id": "onboarding-step-005",
            "stage_name": "Customer household details",
            "description_for_llm": "customer household details, customer household details",
            "action_type": "USER_BASIC_DEtAILS",
            "preconditions": ["user_is_logged_in"],
            "next_action_id_success": "onboarding-step-006",
            "next_action_id_failure": "onboarding-step-005",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "household__first_name",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Household First Name",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid household first format"
                        }
                    },
                    {
                        "field_id": "household_second_name",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Household Second Name",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid household second name format"
                        }
                    },
                    {
                        "field_id": "relationship",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Pincode",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid relationship format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/household-details",
                    "request_payload_template": {
                        "pan": "{{first_name}}",
                        "aadhaar": "{{second_name}}",
                        "pincode": "{{pincode}}"
                    }
                }
            ]
        },
        {
            "action_id": "onboarding-step-006",
            "stage_name": "Customer curent address details",
            "description_for_llm": "customer curent address details, customer current address details",
            "action_type": "USER_Curent_Address_DEtAILS",
            "preconditions": ["user_is_logged_in"],
            "next_action_id_success": "onboarding-step-007",
            "next_action_id_failure": "onboarding-step-006",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "house_number",
                        "component_type": "text_input",
                        "properties": {
                            "label": "",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid household first format"
                        }
                    },
                    {
                        "field_id": "address_line1",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 1",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 1 format"
                        }
                    },
                    {
                        "field_id": "address_line2",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 2",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 2 format"
                        }
                    },
                    {
                        "field_id": "address_line3",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 1",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 3 format"
                        }
                    },
                    {
                        "field_id": "city",
                        "component_type": "text_input",
                        "properties": {
                            "label": "City",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid city format"
                        }
                    },
                    {
                        "field_id": "state",
                        "component_type": "text_input",
                        "properties": {
                            "label": "State",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid state format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/current-address-details",
                    "request_payload_template": {
                        "pan": "{{first_name}}",
                        "aadhaar": "{{second_name}}",
                        "pincode": "{{pincode}}"
                    }
                }
            ]
        },
        {
            "action_id": "onboarding-step-007",
            "stage_name": "Customer curent address details",
            "description_for_llm": "customer curent address details, customer current address details",
            "action_type": "USER_Curent_Address_DEtAILS",
            "preconditions": ["user_is_logged_in"],
            "next_action_id_success": "onboarding-step-008",
            "next_action_id_failure": "onboarding-step-007",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "house_number",
                        "component_type": "text_input",
                        "properties": {
                            "label": "",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid household first format"
                        }
                    },
                    {
                        "field_id": "address_line1",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 1",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 1 format"
                        }
                    },
                    {
                        "field_id": "address_line2",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 2",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 2 format"
                        }
                    },
                    {
                        "field_id": "address_line3",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 1",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 3 format"
                        }
                    },
                    {
                        "field_id": "city",
                        "component_type": "text_input",
                        "properties": {
                            "label": "City",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid city format"
                        }
                    },
                    {
                        "field_id": "state",
                        "component_type": "text_input",
                        "properties": {
                            "label": "State",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid state format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/current-address-details",
                    "request_payload_template": {
                        "pan": "{{first_name}}",
                        "aadhaar": "{{second_name}}",
                        "pincode": "{{pincode}}"
                    }
                }
            ]
        },
        {
            "action_id": "onboarding-step-008",
            "stage_name": "Customer bank details",
            "description_for_llm": "customer cbank details,"
            " bank details",
            "action_type": "USER_Curent_Address_DEtAILS",
            "preconditions": ["user_is_logged_in"],
            "next_action_id_success": "onboarding-step-008",
            "next_action_id_failure": "onboarding-step-007",
            "ui_definition": {
                "step_title": "Customer onboarding",
                "bot_message": "Please onboard customer.",
                "form_fields": [
                    {
                        "field_id": "house_number",
                        "component_type": "text_input",
                        "properties": {
                            "label": "",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid household first format"
                        }
                    },
                    {
                        "field_id": "address_line1",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 1",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 1 format"
                        }
                    },
                    {
                        "field_id": "address_line2",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 2",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 2 format"
                        }
                    },
                    {
                        "field_id": "address_line3",
                        "component_type": "text_input",
                        "properties": {
                            "label": "Address Line 1",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid address line 3 format"
                        }
                    },
                    {
                        "field_id": "city",
                        "component_type": "text_input",
                        "properties": {
                            "label": "City",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid city format"
                        }
                    },
                    {
                        "field_id": "state",
                        "component_type": "text_input",
                        "properties": {
                            "label": "State",
                            "required": True,
                            "validation_pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}",
                            "validation_message": "Invalid state format"
                        }
                    }
                ],
                "submit_button": {"text": "Verify"}
            },
            "api_call_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/current-address-details",
                    "request_payload_template": {
                        "pan": "{{first_name}}",
                        "aadhaar": "{{second_name}}",
                        "pincode": "{{pincode}}"
                    }
                }
            ]
        },
]