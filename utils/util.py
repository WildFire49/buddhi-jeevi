import time
import copy

CURRENT_TIMESTAMP = str(int(time.time()))

def update_component_ids(components):
    collect_fields = set()
    id_map = {}

    # First pass: collect all fields in collect_fields
    def collect_fields_values(component):
        if isinstance(component, dict):
            action = component.get("properties", {}).get("action", {})
            fields = action.get("collect_fields", [])
            for field in fields:
                collect_fields.add(field)
            for key in component:
                collect_fields_values(component[key])
        elif isinstance(component, list):
            for item in component:
                collect_fields_values(item)

    collect_fields_values(components)

    # Second pass: update all id fields and build id_map
    def update_ids_and_map(component):
        if isinstance(component, dict):
            if "id" in component and isinstance(component["id"], str):
                original_id = component["id"]
                new_id = f"{original_id}${CURRENT_TIMESTAMP}"
                id_map[original_id] = new_id
                component["id"] = new_id
            for key in component:
                component[key] = update_ids_and_map(component[key])
        elif isinstance(component, list):
            return [update_ids_and_map(item) for item in component]
        return component

    updated_components = update_ids_and_map(copy.deepcopy(components))

    # Third pass: update collect_fields values using id_map
    def update_collect_fields(component):
        if isinstance(component, dict):
            action = component.get("properties", {}).get("action", {})
            if "collect_fields" in action:
                action["collect_fields"] = [id_map.get(f, f) for f in action["collect_fields"]]
            for key in component:
                component[key] = update_collect_fields(component[key])
        elif isinstance(component, list):
            return [update_collect_fields(item) for item in component]
        return component

    updated_components = update_collect_fields(updated_components)
    return updated_components
