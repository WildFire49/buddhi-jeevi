#!/usr/bin/env python3
import requests
import json
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the actual translation API response structure based on the observed response
class TranslationResponseInput(BaseModel):
    """Class representing the input field in the translation API response"""
    text: str
    audio_url: Optional[str] = None
    target_lang: str
    detected_lang: str
    english_input: str
    english_response: str
    translated_text: str
    audio_response_path: str
    
    # Fields from the RAG response structure based on memory
    ui_components: Optional[List[Dict[str, Any]]] = None
    nlp_response: Optional[str] = None
    response: Optional[Dict[str, Any]] = None

class TranslationResponse(BaseModel):
    """Class representing the complete translation API response"""
    tool: str
    type: str
    input: TranslationResponseInput

# Example of actual translation API response
SAMPLE_RESPONSE = {
    "tool": "translate",
    "type": "text",
    "input": {
        "text": "Hello, how are you today?",
        "audio_url": None,
        "target_lang": "en",
        "detected_lang": "english",
        "translated_text": "Hello! I'm here to assist you with your joint loan application process. How can I help you today?",
        "english_input": "Hello, how are you today?",
        "english_response": "Hello! I'm here to assist you with your joint loan application process. How can I help you today?",
        "audio_response_path": "http://localhost:8004/static/audio/output_b9d5b31e-66cd-43bd-8d59-c859d7a23f5d.mp3"
    }
}

def process_translation_response(response_json: Dict[str, Any]) -> TranslationResponse:
    """Process the translation API response into a structured class"""
    # Parse the response directly into our TranslationResponse class
    return TranslationResponse(**response_json)

# Example usage
def translator(text: str):
    
    # Make a live API call to get a real response
    try:
        print("\nMaking live API call...")
        api_response = requests.post(
            "http://localhost:8004/translate",
            headers={"Content-Type": "application/json"},
            json={
                "tool": "translate",
                "type": "text",
                "input": {
                    "text": text,
                    "target_lang": "en"
                }
            }
        )
        
        # Process the live response
        if api_response.status_code == 200:
            live_response = process_translation_response(api_response.json())
            print("\nLive API Response:")
            print(f"Input: {live_response.input.text}")
            print(f"Detected Language: {live_response.input.detected_lang}")
            print(f"Response: {live_response.input.translated_text[:100]}...")
            print(f"Audio URL: {live_response.input.audio_response_path}")
            return live_response.input
        else:
            print(f"API call failed with status code: {api_response.status_code}")
            res = TranslationResponseInput(text=text, detected_lang="english", translated_text=text, english_input=text, english_response=text, audio_response_path="")
            return res
    except Exception as e:
        print(f"Error making API call: {e}")
        res = TranslationResponseInput(text=text, detected_lang="english", translated_text=text, english_input=text, english_response=text, audio_response_path="")
        return res



