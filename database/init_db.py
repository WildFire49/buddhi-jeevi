import logging
from database.models import Base, get_database_url, UIComponent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database by creating all tables"""
    try:
        # Create database engine
        engine = create_engine(get_database_url())
        
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        return engine
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def create_ui_component_helper(ui_schema):
    """Helper function to create or update a UI component schema
    
    Args:
        ui_schema: Dictionary containing UI schema data
            Required keys: id, type, screen_id, ui_components
    
    Returns:
        The created or updated UIComponent instance
    """
    try:
        # Initialize database and create session
        engine = init_database()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Use the upsert method from UIComponent
        component = UIComponent.upsert(session, ui_schema)
        
        # Close session
        session.close()
        
        return component
    except Exception as e:
        logger.error(f"Error creating UI schema: {str(e)}")
        raise

def bulk_create_ui_components(ui_schemas):
    """Helper function to create or update multiple UI schemas
    
    Args:
        ui_schemas: List of dictionaries containing UI schema data
            Required keys: id, type, screen_id, ui_components
    
    Returns:
        List of created or updated UIComponent instances
    """
    try:
        # Initialize database and create session
        engine = init_database()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Use the bulk_upsert method from UIComponent
        components = UIComponent.bulk_upsert(session, ui_schemas)
        
        # Close session
        session.close()
        
        return components
    except Exception as e:
        logger.error(f"Error bulk creating UI schemas: {str(e)}")
        raise

def main():
    logger.info("Creating database tables...")
    init_database()
    logger.info("Database tables created successfully!")

if __name__ == "__main__":
    main()
