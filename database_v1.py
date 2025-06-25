def get_action_schema():
    return [
    {
        "id": "welcome",
        "stage_name": "Welcome Screen",
        "desc_for_llm": "Simple welcome screen with app name and proceed button., hey, hello, goodmornig",
        "action_type": "WELCOME_SCREEN",
        "next_err_action_id": "error-screen",
        "next_success_action_id": "login-screen",
        "ui_id": "ui_welcome_screen_001",
        "api_detail_id": None
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
        }
    ]