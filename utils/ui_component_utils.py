import logging
from typing import Dict, List, Any, Optional
from database.models import UIComponent, get_db_session

logger = logging.getLogger(__name__)

def store_ui_schema(ui_schema: Dict[str, Any]) -> Optional[UIComponent]:
    """
    Store a UI schema in the database
    
    Args:
        ui_schema: Dictionary with UI schema data from database_v2.py
            Required keys: id, ui_components
            
    Returns:
        UIComponent object or None if error
    """
    try:
        # Validate required fields
        if 'id' not in ui_schema:
            logger.error("Missing required field 'id' in UI schema")
            return None
        if 'ui_components' not in ui_schema:
            logger.error("Missing required field 'ui_components' in UI schema")
            return None
        
        # Create properly formatted schema for database
        db_schema = {
            'id': ui_schema['id'],
            'type': ui_schema.get('type', 'UI'),
            'screen_id': ui_schema.get('screen_id'),
            'ui_components': ui_schema['ui_components']
        }
        
        # Store the UI schema
        session = get_db_session()
        component = UIComponent.upsert(session, db_schema)
        session.close()
        return component
    except Exception as e:
        logger.error(f"Error storing UI schema: {str(e)}")
        return None

def store_ui_schemas(ui_schemas: List[Dict[str, Any]]) -> List[UIComponent]:
    """
    Store multiple UI schemas in the database
    
    Args:
        ui_schemas: List of dictionaries with UI schema data from database_v2.py
            
    Returns:
        List of UIComponent objects
    """
    try:
        # Format schemas for database storage
        db_schemas = []
        for schema in ui_schemas:
            # Check required fields
            if 'id' not in schema:
                logger.warning(f"Skipping UI schema missing 'id'")
                continue
            if 'ui_components' not in schema:
                logger.warning(f"Skipping UI schema missing 'ui_components': {schema['id']}")
                continue
                
            # Create properly formatted schema for database
            db_schema = {
                'id': schema['id'],
                'type': schema.get('type', 'UI'),
                'screen_id': schema.get('screen_id'),
                'ui_components': schema['ui_components']
            }
            db_schemas.append(db_schema)
        
        # Store all valid schemas
        if db_schemas:
            session = get_db_session()
            components = UIComponent.bulk_upsert(session, db_schemas)
            session.close()
            return components
        return []
    except Exception as e:
        logger.error(f"Error storing UI schemas: {str(e)}")
        return []

def get_ui_schema_by_id(schema_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a UI schema by its ID
    
    Args:
        schema_id: Schema ID
            
    Returns:
        UI schema dictionary or None if not found
    """
    try:
        session = get_db_session()
        ui_component = session.query(UIComponent).filter(UIComponent.id == schema_id).first()
        session.close()
        
        if ui_component:
            return {
                'id': ui_component.id,
                'type': ui_component.type,
                'screen_id': ui_component.screen_id,
                'ui_components': ui_component.ui_components
            }
        return None
    except Exception as e:
        logger.error(f"Error getting UI schema {schema_id}: {str(e)}")
        return None

def get_ui_schemas_by_screen(screen_id: str) -> List[Dict[str, Any]]:
    """
    Get UI schemas for a specific screen
    
    Args:
        screen_id: Screen ID
            
    Returns:
        List of UI schema dictionaries
    """
    try:
        session = get_db_session()
        ui_components = session.query(UIComponent).filter(UIComponent.screen_id == screen_id).all()
        session.close()
        
        return [{
            'id': component.id,
            'type': component.type,
            'screen_id': component.screen_id,
            'ui_components': component.ui_components
        } for component in ui_components]
    except Exception as e:
        logger.error(f"Error getting UI schemas for screen {screen_id}: {str(e)}")
        return []

def update_ui_schema(schema_id: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update an existing UI schema
    
    Args:
        schema_id: Schema ID to update
        updated_data: Dictionary with updated data
            
    Returns:
        Updated UI schema dictionary or None if error
    """
    try:
        session = get_db_session()
        ui_component = session.query(UIComponent).filter(UIComponent.id == schema_id).first()
        
        if not ui_component:
            logger.warning(f"UI schema {schema_id} not found for update")
            session.close()
            return None
        
        # Update fields
        for key, value in updated_data.items():
            if hasattr(ui_component, key):
                setattr(ui_component, key, value)
        
        session.commit()
        
        # Return updated schema
        result = {
            'id': ui_component.id,
            'type': ui_component.type,
            'screen_id': ui_component.screen_id,
            'ui_components': ui_component.ui_components
        }
        
        session.close()
        return result
    except Exception as e:
        logger.error(f"Error updating UI schema {schema_id}: {str(e)}")
        return None

def delete_ui_schema(schema_id: str) -> bool:
    """
    Delete a UI schema by its ID
    
    Args:
        schema_id: Schema ID
            
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        session = get_db_session()
        ui_component = session.query(UIComponent).filter(UIComponent.id == schema_id).first()
        
        if not ui_component:
            logger.warning(f"UI schema {schema_id} not found for deletion")
            session.close()
            return False
        
        session.delete(ui_component)
        session.commit()
        session.close()
        
        logger.info(f"Deleted UI schema {schema_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting UI schema {schema_id}: {str(e)}")
        return False


def fetch_ui_component_by_id(schema_id: str) -> Optional[UIComponent]:
    """
    Fetch a UI component by its ID, returning the actual UIComponent object
    
    Args:
        schema_id: Schema ID
            
    Returns:
        UIComponent object or None if not found
    """
    if not schema_id:
        logger.error("Empty schema_id provided to fetch_ui_component_by_id")
        return None
        
    try:
        session = get_db_session()
        
        # Log the search attempt
        logger.info(f"Searching for UI component with id: '{schema_id}'")
        
        # Try exact match first
        ui_component = session.query(UIComponent).filter(UIComponent.id == schema_id).first()
        
        # If not found, try case-insensitive match
        if not ui_component:
            logger.info(f"Exact match not found, trying case-insensitive match")
            # Get all components and check manually (not efficient but helps debug)
            all_components = session.query(UIComponent).all()
            logger.info(f"Found {len(all_components)} total UI components in database")
            
            # Log the first few IDs for debugging
            for i, comp in enumerate(all_components[:5]):
                logger.info(f"DB component {i}: id='{comp.id}', type='{comp.type}'")
            
            # Try to find a case-insensitive match
            for comp in all_components:
                if comp.id.lower() == schema_id.lower():
                    ui_component = comp
                    logger.info(f"Found case-insensitive match: '{comp.id}'")
                    break
        
        session.close()
        
        if ui_component:
            logger.info(f"Successfully found UI component: {ui_component.id}")
        else:
            logger.warning(f"UI component with id '{schema_id}' not found in database")
            
        return ui_component
    except Exception as e:
        logger.error(f"Error fetching UI component {schema_id}: {str(e)}")
        return None


def debug_ui_components() -> List[Dict[str, Any]]:
    """
    Debug function to list all UI components in the database
    
    Returns:
        List of dictionaries with UI component information
    """
    try:
        session = get_db_session()
        components = session.query(UIComponent).all()
        session.close()
        
        result = []
        for comp in components:
            result.append({
                'id': comp.id,
                'type': comp.type,
                'screen_id': comp.screen_id
            })
            
        logger.info(f"Found {len(result)} UI components in database")
        for i, comp in enumerate(result):
            logger.info(f"Component {i}: id='{comp['id']}', type='{comp['type']}', screen_id='{comp['screen_id']}'")
            
        return result
    except Exception as e:
        logger.error(f"Error debugging UI components: {str(e)}")
        return []
