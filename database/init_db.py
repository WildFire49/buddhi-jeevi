import logging
from database.models import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Creating database tables...")
    init_db()
    logger.info("Database tables created successfully!")

if __name__ == "__main__":
    main()
