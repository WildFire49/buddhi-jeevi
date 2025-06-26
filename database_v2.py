def get_action_schema():
    return [
    {
        "id": "welcome",
        "stage_name": "Welcome Screen",
        "desc_for_llm": "Simple welcome screen with app name and proceed button., hey, hello, goodmornig",
        "action_type": "WELCOME_SCREEN",
        "next_err_action_id": "welcome",
        "next_success_action_id": "select-flow",
        "ui_id": "ui_welcome_screen_001",
        "api_detail_id": None
    },
    {
        "id": "select-flow",
        "stage_name": "Select Flow",
        "desc_for_llm": "Screen that allows the user to select either the Onboarding or Collections flow.",
        "action_type": "FLOW_SELECTION_SCREEN",
        "next_err_action_id": "select-flow",
        "next_success_action_id": "video-consent",
        "ui_id": "ui_select_flow_001",
        "api_detail_id": "api_select_flow_001"
    },
    {
        "id": "video-consent",
        "stage_name": "Video Consent",
        "desc_for_llm": "Consent screen with video component and a button to capture user agreement after viewing.",
        "action_type": "VIDEO_CONSENT_SCREEN",
        "next_err_action_id": "video-consent",
        "next_success_action_id": "mobile-verification",
        "ui_id": "ui_video_consent_001",
        "api_detail_id": "api_video_consent_001"
    },
    {
        "id": "mobile-verification",
        "stage_name": "Mobile Number Verification",
        "desc_for_llm": "Screen for verifying customer's mobile number. Takes 10-digit input and validates.",
        "action_type": "MOBILE_VERIFICATION_SCREEN",
        "next_err_action_id": "verification-error-screen",
        "next_success_action_id": "otp-verification-screen",
        "ui_id": "ui_mobile_verification_001",
        "api_detail_id": "api_mobile_verification_001"
    },
    {
        "id": "otp-verification",
        "stage_name": "OTP Verification Screen",
        "desc_for_llm": "Screen for entering OTP sent to user's mobile number.",
        "action_type": "OTP_VERIFICATION_SCREEN",
        "next_err_action_id": "otp-verification",
        "next_success_action_id": "prospect-info",
        "ui_id": "ui_otp_verification_001",
        "api_detail_id": "api_otp_verification_001"
    },
    {
        "id": "prospect-info",
        "stage_name": "Prospect Info",
        "desc_for_llm": "Screen to confirm secondary KYC using a document dropdown.",
        "action_type": "PROSPECT_INFO_SCREEN",
        "next_err_action_id": "prospect-info",
        "next_success_action_id": "video-consent",
        "ui_id": "ui_prospect_info_001",
        "api_detail_id": "api_prospect_info_001"
    },
    {
        "id": "login",
        "stage_name": "Login Screen",
        "desc_for_llm": "User login screen with username and password inputs.",
        "action_type": "LOGIN_SCREEN",
        "next_err_action_id": "login-error-screen",
        "next_success_action_id": "user-details-screen",
        "ui_id": "ui_login_screen_001",
        "api_detail_id": "api_login_001"
    },
    {
        "id": "user-details",
        "stage_name": "User Details Screen",
        "desc_for_llm": "User details collection screen for customer name and mobile number.",
        "action_type": "USER_DETAILS_SCREEN",
        "next_err_action_id": "details-error-screen",
        "next_success_action_id": "dashboard-screen",
        "ui_id": "ui_user_details_001",
        "api_detail_id": "api_user_details_001"
    }
]



def get_ui_schema():
    return [
        {
            "id": "ui_welcome_screen_001",
            "type": "UI",
            "session_id": "session_welcome_001",
            "screen_id": "welcome_screen",
            "ui_components": [
                {
                    "id": "header_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "16dp",
                        "background_color": "#FFFFFF",
                        "vertical_arrangement": "center",
                        "horizontal_alignment": "center"
                    },
                    "children": [
                        {
                            "id": "welcome_text",
                            "component_type": "text",
                            "properties": {
                                "text": "Welcome to MiFix",
                                "text_size": "24sp",
                                "text_color": "#000000",
                                "text_style": "bold",
                                "text_align": "center",
                                "margin_bottom": "48dp"
                            }
                        }
                    ]
                },
                {
                    "id": "button_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "16dp",
                        "horizontal_alignment": "stretch"
                    },
                    "children": [
                        {
                            "id": "proceed_button",
                            "component_type": "button",
                            "properties": {
                                "text": "Proceed",
                                "background_color": "#007AFF",
                                "text_color": "#FFFFFF",
                                "text_size": "16sp",
                                "text_style": "bold",
                                "corner_radius": "8dp",
                                "padding": "16dp",
                                "action": {
                                    "type": "navigate_to",
                                    "screen": "login-screen"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        {
            "id": "ui_video_consent_001",
            "session_id": "session_video_consent_001",
            "screen_id": "video_consent_screen",
            "ui_components": [
                {
                    "id": "main_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "24dp",
                        "background_color": "#F5F5F5",
                        "vertical_arrangement": "center",
                        "horizontal_alignment": "stretch"
                    },
                    "children": [
                        {
                            "id": "video_consent_heading",
                            "component_type": "text",
                            "properties": {
                                "text": "Video Consent",
                                "text_size": "24sp",
                                "text_color": "#000000",
                                "text_style": "bold",
                                "text_align": "center",
                                "margin_bottom": "12dp"
                            }
                        },
                        {
                            "id": "consent_instruction",
                            "component_type": "text",
                            "properties": {
                                "text": "Show this video to the customer",
                                "text_size": "16sp",
                                "text_color": "#333333",
                                "text_align": "center",
                                "margin_bottom": "16dp"
                            }
                        },
                        {
                            "id": "video_player",
                            "component_type": "video",
                            "properties": {
                                "video_url": "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4",
                                "thumbnail_url": "https://example.com/video-thumbnail.jpg",
                                "background_color": "#000000",
                                "corner_radius": "12dp",
                                "aspect_ratio": "16:9",
                                "margin_bottom": "20dp",
                                "action": {
                                    "type": "play_video"
                                }
                            }
                        },
                        {
                            "id": "accept_button",
                            "component_type": "button",
                            "properties": {
                                "text": "Capture Customer Consent",
                                "background_color": "#007AFF",
                                "text_color": "#FFFFFF",
                                "text_size": "16sp",
                                "text_style": "semibold",
                                "corner_radius": "12dp",
                                "padding": "16dp",
                                "enabled": True,
                                "action": {
                                    "type": "submit_form",
                                    "endpoint": "/api/accept-consent",
                                    "method": "POST"
                                }
                            }
                        }
                    ]
                }
            ]
        },
        {
            "id": "ui_login_screen_001",
            "session_id": "session_login_001",
            "screen_id": "login_screen",
            "ui_components": [
                {
                    "id": "header_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "16dp",
                        "background_color": "#FFFFFF",
                        "vertical_arrangement": "top",
                        "horizontal_alignment": "center"
                    },
                    "children": [
                        {
                            "id": "login_title",
                            "component_type": "text",
                            "properties": {
                                "text": "Login",
                                "text_size": "24sp",
                                "text_color": "#000000",
                                "text_style": "bold",
                                "text_align": "center",
                                "margin_bottom": "24dp"
                            }
                        }
                    ]
                },
                {
                    "id": "form_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "16dp",
                        "vertical_arrangement": "top",
                        "horizontal_alignment": "stretch"
                    },
                    "children": [
                        {
                            "id": "username",
                            "component_type": "text_input",
                            "properties": {
                                "hint": "Enter your username",
                                "text_size": "16sp",
                                "background_color": "#F5F5F5",
                                "corner_radius": "8dp",
                                "padding": "12dp",
                                "margin_bottom": "16dp",
                                "input_type": "text",
                                "max_length": 50,
                                "validation": {
                                    "required": True,
                                    "min_length": 3,
                                    "pattern": "^[a-zA-Z0-9_]+$",
                                    "custom_error": "Username should only contain letters, numbers and underscore"
                                }
                            }
                        },
                        {
                            "id": "password",
                            "component_type": "text_input",
                            "properties": {
                                "hint": "Enter your password",
                                "text_size": "16sp",
                                "background_color": "#F5F5F5",
                                "corner_radius": "8dp",
                                "padding": "12dp",
                                "margin_bottom": "24dp",
                                "input_type": "password",
                                "validation": {
                                    "required": True,
                                    "min_length": 6,
                                    "pattern": "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$",
                                    "custom_error": "Password must contain uppercase, lowercase, number and special character"
                                }
                            }
                        }
                    ]
                },
                {
                    "id": "button_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "16dp",
                        "horizontal_alignment": "stretch"
                    },
                    "children": [
                        {
                            "id": "login_button",
                            "component_type": "button",
                            "properties": {
                                "text": "Login",
                                "background_color": "#007AFF",
                                "text_color": "#FFFFFF",
                                "text_size": "16sp",
                                "text_style": "bold",
                                "corner_radius": "8dp",
                                "padding": "16dp",
                                "action": {
                                    "type": "submit_form",
                                    "endpoint": "/api/login",
                                    "method": "POST",
                                    "collect_fields": ["username", "password"]
                                }
                            }
                        }
                    ]
                }
            ]
        },
        {
            "id": "ui_user_details_001",
            "session_id": "session_details_001",
            "screen_id": "user_details_screen",
            "ui_components": [
                {
                    "id": "header_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "16dp",
                        "background_color": "#FFFFFF",
                        "vertical_arrangement": "top",
                        "horizontal_alignment": "center"
                    },
                    "children": [
                        {
                            "id": "details_title",
                            "component_type": "text",
                            "properties": {
                                "text": "User Details",
                                "text_size": "24sp",
                                "text_color": "#000000",
                                "text_style": "bold",
                                "text_align": "center",
                                "margin_bottom": "16dp"
                            }
                        },
                        {
                            "id": "description_text",
                            "component_type": "text",
                            "properties": {
                                "text": "Please fill in your information",
                                "text_size": "16sp",
                                "text_color": "#666666",
                                "text_align": "center",
                                "margin_bottom": "24dp"
                            }
                        }
                    ]
                },
                {
                    "id": "form_container",
                    "component_type": "column",
                    "properties": {
                        "padding": "16dp",
                        "vertical_arrangement": "top",
                        "horizontal_alignment": "stretch"
                    },
                    "children": [
                        {
                            "id": "customer_name",
                            "component_type": "text_input",
                            "properties": {
                                "hint": "Enter your name",
                                "text_size": "16sp",
                                "background_color": "#F5F5F5",
                                "corner_radius": "8dp",
                                "padding": "12dp",
                                "margin_bottom": "16dp",
                                "input_type": "text",
                                "max_length": 50,
                                "validation": {
                                    "required": True,
                                    "min_length": 2,
                                    "pattern": "^[a-zA-Z\s]+$",
                                    "custom_error": "Name should only contain letters and spaces"
                                }
                            }
                        },
                        {
                            "id": "mobile_number",
                            "component_type": "text_input",
                            "properties": {
                                "hint": "Enter your phone number",
                                "text_size": "16sp",
                                "background_color": "#F5F5F5",
                                "corner_radius": "8dp",
                                "padding": "12dp",
                                "margin_bottom": "24dp",
                                "input_type": "phone",
                                "max_length": 10,
                                "validation": {
                                    "required": True,
                                    "pattern": "^[0-9]{10}$",
                                    "custom_error": "Please enter a valid 10-digit phone number"
                                }
                            }
                        }
                    ]
                },
                {
                    "id": "button_container",
                    "component_type": "row",
                    "properties": {
                        "padding": "16dp",
                        "horizontal_arrangement": "space_between"
                    },
                    "children": [
                        {
                            "id": "submit_button",
                            "component_type": "button",
                            "properties": {
                                "text": "Submit",
                                "background_color": "#007AFF",
                                "text_color": "#FFFFFF",
                                "text_size": "16sp",
                                "text_style": "bold",
                                "corner_radius": "8dp",
                                "padding": "16dp",
                                "weight": 1,
                                "margin_start": "8dp",
                                "action": {
                                    "type": "submit_form",
                                    "endpoint": "/api/user-details",
                                    "method": "POST",
                                    "collect_fields": ["customer_name", "mobile_number"]
                                }
                            }
                        }
                    ]
                },
                {
                    "id": "ui_mobile_verification_001",
                    "session_id": "session_mobile_verification_001",
                    "screen_id": "mobile_verification_screen",
                    "ui_components": [
                        {
                            "id": "header_container",
                            "component_type": "column",
                            "properties": {
                                "padding": "16dp",
                                "background_color": "#FFFFFF",
                                "vertical_arrangement": "top",
                                "horizontal_alignment": "center"
                            },
                            "children": [
                                {
                                    "id": "verification_title",
                                    "component_type": "text",
                                    "properties": {
                                        "text": "Add Customer Mobile Number",
                                        "text_size": "24sp",
                                        "text_color": "#000000",
                                        "text_style": "bold",
                                        "text_align": "center",
                                        "margin_bottom": "24dp"
                                    }
                                }
                            ]   
                        },
                        {
                            "id": "form_container",
                            "component_type": "column",
                            "properties": {
                                "padding": "16dp",
                                "vertical_arrangement": "top",
                                "horizontal_alignment": "stretch"
                            },
                            "children": [
                                {
                                    "id": "mobile_number_input",
                                    "component_type": "text_input",
                                    "properties": {
                                        "hint": "Enter Mobile Number",
                                        "text_size": "16sp",
                                        "background_color": "#F5F5F5",
                                        "corner_radius": "8dp",
                                        "padding": "12dp",
                                        "margin_bottom": "24dp",
                                        "input_type": "phone",
                                        "max_length": 10,
                                        "validation": {
                                            "required": True,
                                            "pattern": "^[0-9]{10}$",
                                            "custom_error": "Enter a valid 10-digit mobile number"
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "ui_otp_verification_001",
                    "session_id": "session_otp_verification_001",
                    "screen_id": "otp_verification_screen",
                    "ui_components": [
                        {
                            "id": "header_container",
                            "component_type": "column",
                            "properties": {
                                "padding": "16dp",
                                "background_color": "#FFFFFF",
                                "vertical_arrangement": "top",
                                "horizontal_alignment": "center"
                            },
                            "children": [
                                {
                                    "id": "otp_title",
                                    "component_type": "text",
                                    "properties": {
                                        "text": "Enter Verification Code",
                                        "text_size": "24sp",
                                        "text_color": "#000000",
                                        "text_style": "bold",
                                        "text_align": "center",
                                        "margin_bottom": "16dp"
                                    }
                                },
                                {
                                    "id": "otp_info_text",
                                    "component_type": "text",
                                    "properties": {
                                        "text": "We have sent the code to your mobile",
                                        "text_size": "16sp",
                                        "text_color": "#666666",
                                        "text_align": "center",
                                        "margin_bottom": "24dp"
                                    }
                                }
                            ]
                        },
                        {
                            "id": "form_container",
                            "component_type": "column",
                            "properties": {
                                "padding": "16dp",
                                "vertical_arrangement": "top",
                                "horizontal_alignment": "stretch"
                            },
                            "children": [
                                {
                                    "id": "otp_input",
                                    "component_type": "text_input",
                                    "properties": {
                                        "hint": "Enter OTP",
                                        "text_size": "16sp",
                                        "background_color": "#F5F5F5",
                                        "corner_radius": "8dp",
                                        "padding": "12dp",
                                        "margin_bottom": "24dp",
                                        "input_type": "number",
                                        "max_length": 6,
                                        "validation": {
                                            "required": True,
                                            "pattern": "^[0-9]{4,6}$",
                                            "custom_error": "Enter a valid 4 to 6 digit OTP"
                                        }
                                    }
                                }
                            ]
                        },
                        {
                            "id": "button_container",
                            "component_type": "column",
                            "properties": {
                                "padding": "16dp",
                                "horizontal_alignment": "stretch"
                            },
                            "children": [
                                {
                                    "id": "verify_otp_button",
                                    "component_type": "button",
                                    "properties": {
                                        "text": "Verify OTP",
                                        "background_color": "#007AFF",
                                        "text_color": "#FFFFFF",
                                        "text_size": "16sp",
                                        "text_style": "bold",
                                        "corner_radius": "8dp",
                                        "padding": "16dp",
                                        "action": {
                                            "type": "submit_form",
                                            "endpoint": "/api/verify-otp",
                                            "method": "POST",
                                            "collect_fields": ["otp_input"]
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "ui_select_flow_001",
                    "session_id": "session_select_flow_001",
                    "screen_id": "select_flow_screen",
                    "ui_components": [
                        {
                            "id": "main_container",
                            "component_type": "column",
                            "properties": {
                                "padding": "20dp",
                                "background_color": "#FFFFFF",
                                "vertical_arrangement": "center",
                                "horizontal_alignment": "stretch"
                            },
                            "children": [
                                {
                                    "id": "flow_title",
                                    "component_type": "text",
                                    "properties": {
                                        "text": "What would you like to do?",
                                        "text_size": "24sp",
                                        "text_color": "#000000",
                                        "text_style": "bold",
                                        "text_align": "center",
                                        "margin_bottom": "32dp"
                                    }
                                },
                                {
                                    "id": "onboarding_button",
                                    "component_type": "button",
                                    "properties": {
                                        "text": "Onboarding",
                                        "background_color": "#007AFF",
                                        "text_color": "#FFFFFF",
                                        "text_size": "16sp",
                                        "corner_radius": "8dp",
                                        "padding": "16dp",
                                        "margin_bottom": "16dp",
                                        "action": {
                                            "type": "submit_form",
                                            "endpoint": "/api/select-flow",
                                            "method": "POST",
                                            "collect_fields": ["flow_choice"],
                                            "extra_payload": {
                                                "flow_choice": "onboarding"
                                            }
                                        }
                                    }
                                },
                                {
                                    "id": "collections_button",
                                    "component_type": "button",
                                    "properties": {
                                        "text": "Collections",
                                        "background_color": "#34C759",
                                        "text_color": "#FFFFFF",
                                        "text_size": "16sp",
                                        "corner_radius": "8dp",
                                        "padding": "16dp",
                                        "action": {
                                            "type": "submit_form",
                                            "endpoint": "/api/select-flow",
                                            "method": "POST",
                                            "collect_fields": ["flow_choice"],
                                            "extra_payload": {
                                                "flow_choice": "collections"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "ui_prospect_info_001",
                    "session_id": "session_prospect_info_001",
                    "screen_id": "prospect_info_screen",
                    "ui_components": [
                        {
                            "id": "main_container",
                            "component_type": "column",
                            "properties": {
                                "padding": "20dp",
                                "background_color": "#FFFFFF",
                                "vertical_arrangement": "top",
                                "horizontal_alignment": "stretch"
                            },
                            "children": [
                                {
                                    "id": "title_text",
                                    "component_type": "text",
                                    "properties": {
                                        "text": "Prospect Info",
                                        "text_size": "24sp",
                                        "text_color": "#000000",
                                        "text_style": "bold",
                                        "text_align": "center",
                                        "margin_bottom": "24dp"
                                    }
                                },
                                {
                                    "id": "kyc_instruction",
                                    "component_type": "text",
                                    "properties": {
                                        "text": "Confirm Secondary KYC",
                                        "text_size": "16sp",
                                        "text_color": "#333333",
                                        "text_align": "left",
                                        "margin_bottom": "16dp"
                                    }
                                },
                                {
                                    "id": "document_dropdown",
                                    "component_type": "dropdown",
                                    "properties": {
                                        "hint": "Select Document",
                                        "title": "Select Document for KYC",
                                        "margin_bottom": "32dp",
                                        "background_color": "#F5F5F5",
                                        "corner_radius": "8dp",
                                        "options": [
                                            {
                                                "value": "",
                                                "label": "-- Select Document --"
                                            },
                                            {
                                                "value": "voter_id",
                                                "label": "Voter ID"
                                            },
                                            {
                                                "value": "pan",
                                                "label": "PAN"
                                            }
                                        ],
                                        "default_value": "",
                                        "validation": {
                                            "required": True,
                                            "custom_error": "Please select a valid document"
                                        }
                                    }
                                },
                                {
                                    "id": "submit_button",
                                    "component_type": "button",
                                    "properties": {
                                        "text": "Submit",
                                        "background_color": "#007AFF",
                                        "text_color": "#FFFFFF",
                                        "text_size": "16sp",
                                        "text_style": "bold",
                                        "corner_radius": "8dp",
                                        "padding": "16dp",
                                        "action": {
                                            "type": "submit_form",
                                            "endpoint": "/api/submit-prospect-info",
                                            "method": "POST",
                                            "collect_fields": ["document_dropdown"]
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]


def get_api_schema():
    return [
        {
            "id": "api_login_001",
            "api_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/api/login",
                    "request_payload_template": {
                        "username": "{{username}}",
                        "password": "{{password}}"
                    }
                }
            ]
        },
        {
            "id": "api_user_details_001",
            "type": "API",
            "api_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/api/user-details",
                    "request_payload_template": {
                        "customer_name": "{{customer_name}}",
                        "mobile_number": "{{mobile_number}}"
                    }
                }
            ]
        },
        {
            "id": "api_mobile_verification_001",
            "type": "API",
            "api_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/api/validate-mobile",
                    "request_payload_template": {
                        "mobile_number": "{{mobile_number_input}}"
                    }
                }
            ]
        },
        {
            "id": "api_otp_verification_001",
            "type": "API",
            "api_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/api/verify-otp",
                    "request_payload_template": {
                        "otp": "{{otp_input}}"
                    }
                }
            ]
        },
        {
            "id": "api_prospect_info_001",
            "type": "API",
            "api_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/api/submit-prospect-info",
                    "request_payload_template": {
                        "document_type": "{{document_dropdown}}"
                    }
                }
            ]
        },
        {
            "id": "api_select_flow_001",
            "type": "API",
            "api_details": [
                {
                    "http_method": "POST",
                    "endpoint_path": "/api/select-flow",
                    "request_payload_template": {
                        "flow_choice": "{{flow_choice}}"
                    }
                }
            ]
        }
    ]
