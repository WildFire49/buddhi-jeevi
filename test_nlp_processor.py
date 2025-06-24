#!/usr/bin/env python3
# test_nlp_processor.py

import os
from nlp_processor import NLProcessor

def test_text_processing():
    """Test text-based language detection and processing."""
    print("Initializing NLProcessor...")
    processor = NLProcessor()
    
    # Test with different languages
    test_texts = [
        "Hello, how can I apply for a loan?",
        "नमस्ते, मैं लोन के लिए कैसे आवेदन कर सकता हूं?",
        "ಹಲೋ, ನಾನು ಸಾಲಕ್ಕಾಗಿ ಹೇಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು?",
        "हॅलो, मी कर्जासाठी कसा अर्ज करू शकतो?",
        "வணக்கம், நான் கடனுக்கு எப்படி விண்ணப்பிக்க முடியும்?"
    ]
    
    print("\n--- Testing Text Processing ---")
    for text in test_texts:
        print(f"\nInput: {text}")
        processed_text, detected_lang = processor.process_text_input(text)
        print(f"Detected Language: {detected_lang}")
        print(f"Processed Text: {processed_text}")

if __name__ == "__main__":
    test_text_processing()
