from weaviate import WeaviateClient, AuthApiKey
import dbdata
from . import schema # Corrected import for schema
import json


client = WeaviateClient.connect_to_local(
    port=8080,
    grpc_port=50051,  # Optional, skip if not using gRPC
    secure=False
)
client.schema.delete_all()  # (optional) clear old schema

client.schema.create(schema.get_weaviate_schema())

action_docs = dbdata.getObjects()
for doc in action_docs:
    client.data_object.create(
        data_object={
            "action_id": doc["action_id"],
            "stage_name": doc["stage_name"],
            "description_for_llm": doc["description_for_llm"],
            "action_type": doc["action_type"],
            "preconditions": doc["preconditions"],
            "next_action_id_success": doc["next_action_id_success"],
            "next_action_id_failure": doc["next_action_id_failure"],
            "ui_definition": json.dumps(doc["ui_definition"]),
            "api_call_details": json.dumps(doc["api_call_details"])
        },
        class_name="ActionStep"
    )
