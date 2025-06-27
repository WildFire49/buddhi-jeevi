#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("services")

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

# Define ports
translation_api_port = int(os.getenv("TRANSLATION_API_PORT", 8004))
server_port = int(os.getenv("SERVER_PORT", 8002))

# Global variables to track processes
processes = []

def start_translation_api():
    """Start the translation API service"""
    logger.info(f"Starting Translation API on port {translation_api_port}")
    # Set the TRANSLATION_API_PORT environment variable
    env = os.environ.copy()
    env["TRANSLATION_API_PORT"] = str(translation_api_port)
    
    cmd = ["python", "run_translation_api.py"]
    process = subprocess.Popen(cmd, env=env)
    processes.append(process)
    logger.info(f"Translation API started with PID {process.pid}")
    return process

def start_main_server():
    """Start the main server"""
    logger.info(f"Starting Main Server on port {server_port}")
    # Set the SERVER_PORT environment variable
    env = os.environ.copy()
    env["SERVER_PORT"] = str(server_port)
    
    cmd = ["python", "server.py"]
    process = subprocess.Popen(cmd, env=env)
    processes.append(process)
    logger.info(f"Main Server started with PID {process.pid}")
    return process

def cleanup(signum, frame):
    """Clean up processes on exit"""
    logger.info("Shutting down services...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            logger.info(f"Terminating process {process.pid}")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.pid} did not terminate gracefully, killing")
                process.kill()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    # Check for required API keys
    missing_keys = []
    if not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.getenv("GEMINI_API_KEY"):
        missing_keys.append("GEMINI_API_KEY")
    
    if missing_keys:
        logger.warning(f"Missing required API keys: {', '.join(missing_keys)}")
        logger.warning("Services will start but some functionality may be limited")
    
    # Start services
    translation_process = start_translation_api()
    
    # Wait a bit for the translation API to start
    time.sleep(2)
    
    # Start the main server
    server_process = start_main_server()
    
    # Keep the script running
    try:
        while True:
            # Check if processes are still running
            if translation_process.poll() is not None:
                logger.error(f"Translation API exited with code {translation_process.returncode}")
                translation_process = start_translation_api()
            
            if server_process.poll() is not None:
                logger.error(f"Main Server exited with code {server_process.returncode}")
                server_process = start_main_server()
            
            time.sleep(5)
    except KeyboardInterrupt:
        cleanup(None, None)
