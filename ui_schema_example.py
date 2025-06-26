import sys
import os
import logging
import json
from database_v2 import get_ui_schema, get_api_schema
from utils.ui_component_utils import store_ui_schemas
from utils.api_schema_utils import store_api_schemas
from database.models import get_db_session, UIComponent, APISchema, init_db

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Initialize the database first
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database tables initialized successfully")
    
    # Get UI schemas from database_v2
    ui_schemas = get_ui_schema()
    logger.info(f"Retrieved {len(ui_schemas)} UI schemas from database_v2")
    
    # Process and store UI schemas
    ui_components = store_ui_schemas(ui_schemas)
    if ui_components:
        logger.info(f"Successfully stored {len(ui_components)} UI schemas")
    else:
        logger.warning("No UI schemas were stored")
    
    # Get API schemas from database_v2
    api_schemas = get_api_schema()
    logger.info(f"Retrieved {len(api_schemas)} API schemas from database_v2")
    
    # Process and store API schemas
    api_components = store_api_schemas(api_schemas)
    if api_components:
        logger.info(f"Successfully stored {len(api_components)} API schemas")
    else:
        logger.warning("No API schemas were stored")
    
    # Query the database to verify storage
    session = get_db_session()
    
    try:
        # Check UI components
        db_ui_components = session.query(UIComponent).all()
        logger.info(f"Total UI components in database: {len(db_ui_components)}")
        for comp in db_ui_components[:3]:  # Show first 3 for brevity
            logger.info(f"UI Component: {comp.id}, Type: {comp.type}, Screen: {comp.screen_id}")
        
        # Check API schemas
        db_api_schemas = session.query(APISchema).all()
        logger.info(f"Total API schemas in database: {len(db_api_schemas)}")
        for schema in db_api_schemas[:3]:  # Show first 3 for brevity
            logger.info(f"API Schema: {schema.id}, Type: {schema.type}")
    except Exception as e:
        logger.error(f"Error querying database: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
