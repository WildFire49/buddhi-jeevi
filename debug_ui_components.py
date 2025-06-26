#!/usr/bin/env python3
import logging
import sys
from utils.ui_component_utils import debug_ui_components, fetch_ui_component_by_id
from database.models import init_db

# Set up logging to console
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Initialize the database if needed
    logger.info("Initializing database...")
    init_db()
    
    # List all UI components in the database
    logger.info("Listing all UI components in the database:")
    components = debug_ui_components()
    
    if not components:
        logger.error("No UI components found in the database!")
        return
    
    # Try to fetch a specific component
    if len(sys.argv) > 1:
        component_id = sys.argv[1]
    else:
        # Use the first component ID from the list
        component_id = components[0]['id']
    
    logger.info(f"Attempting to fetch UI component with ID: {component_id}")
    component = fetch_ui_component_by_id(component_id)
    
    if component:
        logger.info(f"Successfully retrieved component: {component.id}")
        logger.info(f"Type: {component.type}")
        logger.info(f"Screen ID: {component.screen_id}")
        logger.info(f"UI Components: {component.ui_components}")
    else:
        logger.error(f"Failed to retrieve component with ID: {component_id}")

if __name__ == "__main__":
    main()
