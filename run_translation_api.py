#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify that required environment variables are set
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY environment variable is not set.")
    print("Please make sure it's properly set in your .env file.")
    sys.exit(1)

if not os.getenv("GEMINI_API_KEY"):
    print("ERROR: GEMINI_API_KEY environment variable is not set.")
    print("Please make sure it's properly set in your .env file.")
    sys.exit(1)

# Import and run the translation API
import uvicorn
from nlp.translation_api import app

if __name__ == "__main__":
    # Run the translation API server
    port = int(os.getenv("TRANSLATION_API_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
