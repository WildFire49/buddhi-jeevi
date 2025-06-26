from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, JSON, Boolean, ForeignKey, UniqueConstraint, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import os
import json
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy base
Base = declarative_base()

class APILogHistory(Base):
    """Model for storing API call logs"""
    __tablename__ = "api_log_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<APILogHistory(id={self.id}, endpoint={self.endpoint}, method={self.method})>"
    
    @classmethod
    def create_log(cls, session, user_id, endpoint, method, request_data, response_data, status_code):
        """Create a new API log entry"""
        log = cls(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=response_data,
            status_code=status_code
        )
        session.add(log)
        session.commit()
        return log


class UIComponent(Base):
    """Model for storing UI components"""
    __tablename__ = "ui_component_schema"
    
    id = Column(String(255), primary_key=True)                # Primary identifier for the UI component
    type = Column(String(50), nullable=False)                # Type of UI component schema
    screen_id = Column(String(255), nullable=True, index=True)  # Screen ID for grouping components
    ui_components = Column(JSONB, nullable=False)            # All UI components as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add a unique constraint on id
    __table_args__ = (UniqueConstraint('id', name='uix_ui_component_id'),)
    
    def __repr__(self):
        return f"<UIComponent(id={self.id}, type={self.type}, screen_id={self.screen_id})>"
    
    @classmethod
    def upsert(cls, session, component_data):
        """Upsert a UI component (insert if not exists, update if exists)
        
        Args:
            session: SQLAlchemy session
            component_data: Dictionary containing component data
                Required keys: id, type, ui_components
                
        Returns:
            The created or updated UIComponent instance
        """
        try:
            # Check if required fields are present
            if 'id' not in component_data:
                raise ValueError("id is required")
            if 'type' not in component_data:
                raise ValueError("type is required")
            if 'ui_components' not in component_data:
                raise ValueError("ui_components is required")
            
            # Check if component already exists
            existing = session.query(cls).filter_by(id=component_data['id']).first()
            
            if existing:
                # Update existing component
                for key, value in component_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                component = existing
                logger.info(f"Updated UI component: {component_data['id']}")
            else:
                # Create new component
                component = cls(
                    id=component_data['id'],
                    type=component_data['type'],
                    screen_id=component_data.get('screen_id'),
                    ui_components=component_data['ui_components']
                )
                session.add(component)
                logger.info(f"Created new UI component: {component_data['id']}")
            
            session.commit()
            return component
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error upserting UI component: {str(e)}")
            raise
    
    @classmethod
    def bulk_upsert(cls, session, components_data):
        """Bulk upsert multiple UI components
        
        Args:
            session: SQLAlchemy session
            components_data: List of dictionaries containing component data
            
        Returns:
            List of created or updated UIComponent instances
        """
        results = []
        try:
            for component_data in components_data:
                component = cls.upsert(session, component_data)
                results.append(component)
            return results
        except Exception as e:
            session.rollback()
            logger.error(f"Error in bulk upsert: {str(e)}")
            raise
    

class APISchema(Base):
    """Model for storing API schemas"""
    __tablename__ = "api_detail_schemas"
    
    id = Column(String(255), primary_key=True)                # Primary identifier for the API schema
    type = Column(String(50), nullable=False)                # Type of API schema
    api_details = Column(JSONB, nullable=False)              # API details as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add a unique constraint on id
    __table_args__ = (UniqueConstraint('id', name='uix_api_schema_id'),)
    
    def __repr__(self):
        return f"<APISchema(id={self.id}, type={self.type})>"
    
    @classmethod
    def upsert(cls, session, schema_data):
        """Upsert an API schema (insert if not exists, update if exists)
        
        Args:
            session: SQLAlchemy session
            schema_data: Dictionary containing API schema data
                Required keys: id, type, api_details
                
        Returns:
            The created or updated APISchema instance
        """
        try:
            # Check if required fields are present
            if 'id' not in schema_data:
                raise ValueError("id is required")
            if 'type' not in schema_data:
                raise ValueError("type is required")
            if 'api_details' not in schema_data:
                raise ValueError("api_details is required")
            
            # Check if schema already exists
            existing = session.query(cls).filter_by(id=schema_data['id']).first()
            
            if existing:
                # Update existing schema
                for key, value in schema_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                schema = existing
                logger.info(f"Updated API schema: {schema_data['id']}")
            else:
                # Create new schema
                schema = cls(
                    id=schema_data['id'],
                    type=schema_data['type'],
                    api_details=schema_data['api_details']
                )
                session.add(schema)
                logger.info(f"Created new API schema: {schema_data['id']}")
            
            session.commit()
            return schema
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error upserting API schema: {str(e)}")
            raise
    
    @classmethod
    def bulk_upsert(cls, session, schemas_data):
        """Bulk upsert multiple API schemas
        
        Args:
            session: SQLAlchemy session
            schemas_data: List of dictionaries containing API schema data
            
        Returns:
            List of created or updated APISchema instances
        """
        results = []
        try:
            for schema_data in schemas_data:
                schema = cls.upsert(session, schema_data)
                results.append(schema)
            return results
        except Exception as e:
            session.rollback()
            logger.error(f"Error in bulk upsert: {str(e)}")
            raise
    


# Database connection setup
def get_database_url():
    """Get database URL from environment variables"""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "budhhi-jivi")
    password = os.getenv("POSTGRES_PASSWORD", "budhhi-jivi")
    db = os.getenv("POSTGRES_DB", "budhhi-jivi")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

# Create engine and session factory with connection pooling and retry mechanism
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,  # Check connection before using it
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=5,        # Maximum number of connections to keep
    max_overflow=10,    # Maximum number of connections that can be created beyond pool_size
    connect_args={
        "connect_timeout": 10  # Connection timeout in seconds
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database by creating all tables if they don't exist"""
    try:
        # Create tables only if they don't exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'ui_component_schema' not in existing_tables or 'api_detail_schemas' not in existing_tables:
            # Create tables
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        else:
            logger.info("Tables already exist, skipping creation")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        # Don't raise the exception, allow the app to continue

def get_db_session():
    """Get a new database session"""
    session = SessionLocal()
    try:
        return session
    finally:
        session.close()
