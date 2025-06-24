#!/usr/bin/env python3
# nlp_processor.py

import os
import json
import tempfile
import unicodedata
from typing import Dict, Any, Optional, List, Tuple, BinaryIO, Union

import chromadb
import torch
import torchaudio
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Language name to code mapping (for translation)
LANG_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "kannada": "kn",
    "marathi": "mr",
    "tamil": "ta",
}

# Temporary directory for audio file processing
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio")
os.makedirs(TEMP_DIR, exist_ok=True)

class NLProcessor:
    """
    Natural Language Processing service that handles language detection,
    translation, and processing for the chat API.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one instance is created."""
        if cls._instance is None:
            cls._instance = super(NLProcessor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the NLProcessor with necessary models and connections."""
        # Only initialize once
        if not hasattr(self, 'is_initialized'):
            # Connect to ChromaDB
            self.client = chromadb.HttpClient(host="3.6.132.24", port=8000)
            self.collection = self.client.get_or_create_collection("language_embeddings")
            
            # Initialize sentence transformer for embeddings
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Initialize Whisper model for English speech recognition
            print("Loading Whisper model for speech recognition...")
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
            self.whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
                "openai/whisper-small", 
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True
            ).to(self.device)
            self.whisper_processor = AutoProcessor.from_pretrained("openai/whisper-small")
            self.whisper_pipe = pipeline(
                "automatic-speech-recognition",
                model=self.whisper_model,
                tokenizer=self.whisper_processor.tokenizer,
                feature_extractor=self.whisper_processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16,
                device=self.device
            )
            
            self.is_initialized = True
            print("NLProcessor initialized successfully")
    
    def is_latin(self, text: str) -> bool:
        """Check if text is in Latin script."""
        for ch in text:
            if ch.isalpha() and 'LATIN' not in unicodedata.name(ch, ''):
                return False
        return True
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text using vector similarity search.
        
        Args:
            text: Input text to detect language for
            
        Returns:
            Detected language name (e.g., "english", "hindi", etc.)
        """
        try:
            # Generate embedding for the input text
            embedding = self.embedder.encode([text])[0].tolist()
            
            # Query the language_embeddings collection
            result = self.collection.query(
                query_embeddings=[embedding],
                n_results=5  # Get top 5 matches for better accuracy
            )
            
            if not result or not result["metadatas"]:
                print("No language detection results found")
                return "english"  # Default to English
            
            # Count language occurrences in top results for more robust detection
            lang_counts = {}
            for metadata in result["metadatas"][0]:
                lang = metadata["lang"]
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
            # Return the most common language
            detected_lang = max(lang_counts.items(), key=lambda x: x[1])[0]
            print(f"Detected language: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            print(f"Error detecting language: {e}")
            return "english"  # Default to English on error
    
    def process_text_input(self, text: str) -> Tuple[str, str]:
        """
        Process text input by detecting language and preparing for the RAG chain.
        
        Args:
            text: Input text from user
            
        Returns:
            Tuple of (processed_text, detected_language)
        """
        # Detect language
        detected_lang = self.detect_language(text)
        
        # For now, we'll just return the original text and detected language
        # In a full implementation, you might want to translate non-English text
        return text, detected_lang
        
    def process_audio_input(self, audio_file: BinaryIO, filename: str = None) -> Tuple[str, str]:
        """
        Process audio input by saving to disk, transcribing, and detecting language.
        
        Args:
            audio_file: Audio file object
            filename: Optional filename
            
        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        try:
            # Save audio file to disk temporarily
            if not filename:
                filename = f"audio_{os.urandom(4).hex()}.wav"
                
            temp_path = os.path.join(TEMP_DIR, filename)
            with open(temp_path, "wb") as f:
                f.write(audio_file.read())
                
            print(f"Audio saved to {temp_path}")
            
            # Transcribe the audio
            transcription = self.transcribe_audio(temp_path)
            print(f"Transcription: {transcription}")
            
            # Detect language from transcription
            detected_lang = self.detect_language(transcription)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Could not remove temp file {temp_path}: {e}")
                
            return transcription, detected_lang
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return "", "english"  # Default fallback
            
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio using Whisper model.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            # Use Whisper for transcription
            result = self.whisper_pipe(audio_path)
            transcription = result["text"]
            return transcription.strip()
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""  # Return empty string on error
    
    def get_language_code(self, language: str) -> str:
        """Get the ISO language code for the given language name."""
        return LANG_CODE_MAP.get(language.lower(), "en")

# Example usage
if __name__ == "__main__":
    processor = NLProcessor()
    text = "hello how are you"
    processed_text, lang = processor.process_text_input(text)
    print(f"Input: {text}")
    print(f"Processed: {processed_text}")
    print(f"Language: {lang}")
