def get_weaviate_schema():
    """Returns the Weaviate schema as a dictionary."""
    schema = {
        "classes": [
            {
                "class": "ActionStep",
                "description": "A step in the user onboarding or workflow",
                "vectorizer": "text2vec-openai",  # or "none" if you're embedding manually
                "properties": [
                    {
                        "name": "action_id",
                        "dataType": ["string"]
                    },
                    {
                        "name": "stage_name",
                        "dataType": ["string"]
                    },
                    {
                        "name": "description_for_llm",
                        "dataType": ["text"]  # this will be vectorized
                    },
                    {
                        "name": "action_type",
                        "dataType": ["string"]
                    },
                    {
                        "name": "preconditions",
                        "dataType": ["string[]"]
                    },
                    {
                        "name": "next_action_id_success",
                        "dataType": ["string"]
                    },
                    {
                        "name": "next_action_id_failure",
                        "dataType": ["string"]
                    },
                    {
                        "name": "ui_definition",
                        "dataType": ["text"]  # serialize as JSON string
                    },
                    {
                        "name": "api_call_details",
                        "dataType": ["text"]  # serialize as JSON string
                    }
                ]
            }
        ]
    }
    return schema