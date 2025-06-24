#!/usr/bin/env python3
# test_endpoints.py

import requests
import json
import sys
import os

def test_chat_endpoint(prompt):
    """Test the /chat endpoint with a text prompt."""
    url = "http://localhost:8000/chat"
    
    payload = {
        "prompt": prompt,
        "type": "PROMPT",
        "session_id": "test_session"
    }
    
    print(f"\n--- Testing /chat endpoint ---")
    print(f"Sending prompt: {prompt}")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"Response status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_audio_endpoint(audio_file_path):
    """Test the /chat/audio endpoint with an audio file."""
    url = "http://localhost:8000/chat/audio"
    
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return None
    
    print(f"\n--- Testing /chat/audio endpoint ---")
    print(f"Sending audio file: {audio_file_path}")
    
    try:
        files = {"audio": open(audio_file_path, "rb")}
        data = {"session_id": "test_audio_session"}
        
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        print(f"Response status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_endpoints.py text <prompt>")
        print("   or: python test_endpoints.py audio <audio_file_path>")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    if test_type == "text" and len(sys.argv) >= 3:
        test_chat_endpoint(sys.argv[2])
    elif test_type == "audio" and len(sys.argv) >= 3:
        test_audio_endpoint(sys.argv[2])
    else:
        print("Invalid arguments.")
        print("Usage: python test_endpoints.py text <prompt>")
        print("   or: python test_endpoints.py audio <audio_file_path>")
