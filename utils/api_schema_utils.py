import logging
from typing import Dict, List, Any, Optional
from database.models import APISchema, get_db_session

logger = logging.getLogger(__name__)

def store_api_schema(api_schema: Dict[str, Any]) -> Optional[APISchema]:
    """
    Store an API schema in the database
    
    Args:
        api_schema: Dictionary with API schema data from database_v2.py
            Required keys: id, api_details
            
    Returns:
        APISchema object or None if error
    """
    try:
        # Validate required fields
        if 'id' not in api_schema:
            logger.error("Missing required field 'id' in API schema")
            return None
        if 'api_details' not in api_schema:
            logger.error("Missing required field 'api_details' in API schema")
            return None
        
        # Create properly formatted schema for database
        db_schema = {
            'id': api_schema['id'],
            'type': api_schema.get('type', 'API'),
            'api_details': api_schema['api_details']
        }
        
        # Store the API schema
        session = get_db_session()
        schema = APISchema.upsert(session, db_schema)
        session.close()
        return schema
    except Exception as e:
        logger.error(f"Error storing API schema: {str(e)}")
        return None

def store_api_schemas(api_schemas: List[Dict[str, Any]]) -> List[APISchema]:
    """
    Store multiple API schemas in the database
    
    Args:
        api_schemas: List of dictionaries with API schema data from database_v2.py
            
    Returns:
        List of APISchema objects
    """
    try:
        # Format schemas for database storage
        db_schemas = []
        for schema in api_schemas:
            # Check required fields
            if 'id' not in schema:
                logger.warning(f"Skipping API schema missing 'id'")
                continue
            if 'api_details' not in schema:
                logger.warning(f"Skipping API schema missing 'api_details': {schema['id']}")
                continue
                
            # Create properly formatted schema for database
            db_schema = {
                'id': schema['id'],
                'type': schema.get('type', 'API'),
                'api_details': schema['api_details']
            }
            db_schemas.append(db_schema)
        
        # Store all valid schemas
        if db_schemas:
            session = get_db_session()
            schemas = APISchema.bulk_upsert(session, db_schemas)
            session.close()
            return schemas
        return []
    except Exception as e:
        logger.error(f"Error storing API schemas: {str(e)}")
        return []

def get_api_schema_by_id(schema_id: str) -> Optional[Dict[str, Any]]:
    """
    Get an API schema by its ID
    
    Args:
        schema_id: Schema ID
            
    Returns:
        API schema dictionary or None if not found
    """
    try:
        session = get_db_session()
        api_schema = session.query(APISchema).filter(APISchema.id == schema_id).first()
        session.close()
        
        if api_schema:
            return {
                'id': api_schema.id,
                'type': api_schema.type,
                'api_details': api_schema.api_details
            }
        return None
    except Exception as e:
        logger.error(f"Error getting API schema {schema_id}: {str(e)}")
        return None

def get_api_schemas_by_type(schema_type: str) -> List[Dict[str, Any]]:
    """
    Get API schemas by type
    
    Args:
        schema_type: Schema type
            
    Returns:
        List of API schema dictionaries
    """
    try:
        session = get_db_session()
        api_schemas = session.query(APISchema).filter(APISchema.type == schema_type).all()
        session.close()
        
        return [{
            'id': schema.id,
            'type': schema.type,
            'api_details': schema.api_details
        } for schema in api_schemas]
    except Exception as e:
        logger.error(f"Error getting API schemas for type {schema_type}: {str(e)}")
        return []

def update_api_schema(schema_id: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update an existing API schema
    
    Args:
        schema_id: Schema ID to update
        updated_data: Dictionary with updated data
            
    Returns:
        Updated API schema dictionary or None if error
    """
    try:
        session = get_db_session()
        api_schema = session.query(APISchema).filter(APISchema.id == schema_id).first()
        
        if not api_schema:
            logger.warning(f"API schema {schema_id} not found for update")
            session.close()
            return None
        
        # Update fields
        for key, value in updated_data.items():
            if hasattr(api_schema, key):
                setattr(api_schema, key, value)
        
        session.commit()
        
        # Return updated schema
        result = {
            'id': api_schema.id,
            'type': api_schema.type,
            'api_details': api_schema.api_details
        }
        
        session.close()
        return result
    except Exception as e:
        logger.error(f"Error updating API schema {schema_id}: {str(e)}")
        return None

def delete_api_schema(schema_id: str) -> bool:
    """
    Delete an API schema by its ID
    
    Args:
        schema_id: Schema ID
            
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        session = get_db_session()
        api_schema = session.query(APISchema).filter(APISchema.id == schema_id).first()
        
        if not api_schema:
            logger.warning(f"API schema {schema_id} not found for deletion")
            session.close()
            return False
        
        session.delete(api_schema)
        session.commit()
        session.close()
        
        logger.info(f"Deleted API schema {schema_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting API schema {schema_id}: {str(e)}")
        return False
