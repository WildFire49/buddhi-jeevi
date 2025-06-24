def get_action_schema():
    return [
        {
            "action_id":"JLG_S0_A1_LOGIN",
            "stage_name":"Authentication",
            "desc_for_llm":"This is the initial step for a field officer to log in to the system. It requires the employee ID and password.",
            "action_type":"USER_DATA_COLLECTION",
            "next_err_action_id":"JLG_S0_A1_LOGIN",
            "next_success_action_id":"JLG_S0_A1_LOGIN",
            "ui_id":"JLG_S0_A1_LOGIN",
            "api_detail_id":"JLG_S0_A1_LOGIN"
        }
    ]


def get_ui_schema():
    return [
        {
            "ui_id":"JLG_S0_A1_LOGIN",
            "ui_components":[
                {
                    "field_id":"employeeId",
                    "component_type":"Text Input Field",
                    "properties":{
                        "label":"Employee ID",
                        "hint":"Enter your unique employee ID",
                        "input_type":"text",
                        "required":True
                    }
                },
                {
                    "field_id":"password",
                    "component_type":"Password Field",
                    "properties":{
                        "label":"Password",
                        "hint":"Enter your password",
                        "input_type":"password",
                        "required":True
                    }
                }
            ]
        }
    ]

def get_api_schema():
    return [
        {
            "api_detail_id":"JLG_S0_A1_LOGIN",
            "api_details":{
                "http_method":"POST",
                "endpoint_path":"/api/v1/auth/login",
                "request_payload_template":{
                    "employeeId":"string",
                    "password":"string",
                    "deviceUniqueNo":"string"
                }
            }
        }
    ]