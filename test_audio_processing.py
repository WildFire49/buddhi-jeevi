#!/usr/bin/env python3
# test_audio_processing.py

import os
import sys
from nlp_processor import NLProcessor

def test_audio_processing(audio_file_path):
    """Test audio processing and transcription."""
    print("Initializing NLProcessor...")
    processor = NLProcessor()
    
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return
    
    print(f"\n--- Testing Audio Processing ---")
    print(f"Audio file: {audio_file_path}")
    
    # Open the audio file
    with open(audio_file_path, 'rb') as audio_file:
        # Process the audio file
        try:
            transcribed_text, detected_lang = processor.process_audio_input(audio_file, os.path.basename(audio_file_path))
            print(f"Transcription: {transcribed_text}")
            print(f"Detected Language: {detected_lang}")
        except Exception as e:
            print(f"Error processing audio: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_audio_processing.py <path_to_audio_file>")
        sys.exit(1)
    
    test_audio_processing(sys.argv[1])
