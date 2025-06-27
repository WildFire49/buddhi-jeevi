#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set default values for environment variables if not in .env file
if not os.getenv("POSTGRES_HOST"):
    os.environ["POSTGRES_HOST"] = "3.6.132.24"
if not os.getenv("POSTGRES_PORT"):
    os.environ["POSTGRES_PORT"] = "5432"
if not os.getenv("POSTGRES_USER"):
    os.environ["POSTGRES_USER"] = "budhhi-jivi"
if not os.getenv("POSTGRES_DB"):
    os.environ["POSTGRES_DB"] = "budhhi-jivi"

# Import server module after setting environment variables
from server import app
import uvicorn

if __name__ == "__main__":
    # Run the server
    # Use port 8003 to avoid conflict with existing server on port 8002
    port = int(os.getenv("SERVER_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
