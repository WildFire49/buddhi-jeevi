#!/usr/bin/env python3
# generate_test_audio.py

from gtts import gTTS
import os

def generate_test_audio():
    """Generate test audio files in different languages."""
    # Create directory for test audio files
    os.makedirs("test_audio", exist_ok=True)
    
    # Test phrases in different languages
    test_phrases = {
        "english": "Hello, I would like to apply for a loan for my new business.",
        "hindi": "नमस्ते, मैं अपने नए व्यवसाय के लिए ऋण के लिए आवेदन करना चाहता हूं।",
        "tamil": "வணக்கம், எனது புதிய வணிகத்திற்கு கடனுக்கு விண்ணப்பிக்க விரும்புகிறேன்."
    }
    
    # Generate audio files
    for lang, text in test_phrases.items():
        print(f"Generating {lang} audio...")
        tts = gTTS(text=text, lang=lang[:2])  # Use first 2 chars of language code
        filename = f"test_audio/{lang}_sample.mp3"
        tts.save(filename)
        print(f"Saved to {filename}")

if __name__ == "__main__":
    generate_test_audio()
