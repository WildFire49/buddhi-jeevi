#!/usr/bin/env python3
import os
import sys

# Set environment variables to match docker-compose.yml
os.environ["MINIO_ENDPOINT"] = "http://3.6.132.24"
os.environ["MINIO_PORT"] = "9000"
os.environ["MINIO_ACCESS_KEY"] = "SWMSC2SQP1ICJ0I84N81"
os.environ["MINIO_SECRET_KEY"] = "bXwJ+wFwjpb9qP1S85bVsuXceO4oJtNK7+rZCS15"
os.environ["MINIO_BUCKET"] = "llm-recordings"
os.environ["POSTGRES_HOST"] = "3.6.132.24"  # Assuming PostgreSQL is also at the same IP
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "budhhi-jivi"
os.environ["POSTGRES_PASSWORD"] = "budhhi-jivi"
os.environ["POSTGRES_DB"] = "budhhi-jivi"

# Import server module after setting environment variables
from server import app
import uvicorn

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8002)
