from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json

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
    """Initialize database by creating all tables"""
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        # Don't raise the exception, allow the app to continue

def get_db_session():
    """Get a new database session"""
    session = SessionLocal()
    try:
        return session
    finally:
        session.close()
