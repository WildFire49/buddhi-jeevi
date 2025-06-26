from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import requests
import tempfile
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("translation_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("translation_api")

from lang_identifier import transcribe, detect_language
from translator import translate_to_english, translate_back
from llm_client import get_gpt_response
from asr_client import transcribe_audio
from tts import synthesize_and_save_audio

LANG_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "kannada": "kn",
    "marathi": "mr",
    "tamil": "ta",
}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatMessage(BaseModel):
    role: str
    content: str

class TranslationInput(BaseModel):
    text: Optional[str] = None
    audio_url: Optional[str] = None
    target_lang: Optional[str] = "en"
    chat_history: Optional[List[ChatMessage]] = []

class TranslationRequest(BaseModel):
    tool: str
    type: str
    input: TranslationInput

@app.post("/translate")
async def handle_translate(req: TranslationRequest):
    logger.info(f"Received translation request: tool={req.tool}, type={req.type}")
    input_data = req.input
    text = input_data.text
    audio_url = input_data.audio_url
    chat_history = input_data.chat_history or []
    
    logger.debug(f"Input text: {text}")
    logger.debug(f"Audio URL: {audio_url}")
    logger.debug(f"Chat history length: {len(chat_history)}")

    # Transcribe if audio is provided
    if audio_url:
        try:
            logger.info(f"Processing audio input from URL: {audio_url}")
            headers = {
            "User-Agent": "Mozilla/5.0"
            }
            response = requests.get(audio_url, headers=headers, allow_redirects=True)
            if response.status_code != 200:
                logger.error(f"Failed to fetch audio file. Status code: {response.status_code}")
                raise ValueError("Failed to fetch audio file")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(response.content)
                tmp_file.flush()
                audio_path = tmp_file.name
                logger.debug(f"Saved audio to temporary file: {audio_path}")
            logger.info("Transcribing audio...")
            input_text = transcribe(audio_path)
            logger.info(f"Audio transcribed: '{input_text}'")
            os.remove(audio_path)
            input_mode = "voice"
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {e}")
    elif text:
        input_text = text
        input_mode = "text"
        logger.info(f"Processing text input: '{input_text}'")
    else:
        logger.error("No text or audio_url provided in request")
        raise HTTPException(status_code=400, detail="Either 'text' or 'audio_url' must be provided")

    # Detect language
    logger.info("Detecting language...")
    detected_lang = detect_language(input_text)
    lang_code = LANG_CODE_MAP.get(detected_lang.lower(), "en")
    logger.info(f"Detected language: {detected_lang} (code: {lang_code})")

    # If English, go direct to GPT
    if detected_lang == "english":
        logger.info("Input is in English. Sending directly to GPT without translation")
        chat_history.append({"role": "user", "content": input_text})
        logger.info(f"Sending to GPT: '{input_text}'")
        reply = get_gpt_response(chat_history)
        logger.info(f"GPT response: '{reply}'")
        chat_history.append({"role": "assistant", "content": reply})
        logger.info("Synthesizing audio response...")
        audio_path = synthesize_and_save_audio(reply, lang_code)
        audio_url = f"http://localhost:8000{audio_path}"
        logger.info(f"Audio response saved at: {audio_url}")

        return {
            "tool": req.tool,
            "type": req.type,
            "input": {
                "text": input_text,
                "audio_url": input_data.audio_url,
                "target_lang": lang_code,
                "detected_lang": "english",
                "translated_text": reply,
                "english_input": input_text,
                "audio_response_path": audio_url
            }
        }

    # Else translate → GPT → translate back
    if input_mode == "voice":
        logger.info(f"Transcribing audio with detected language: {detected_lang}")
        regional_text = transcribe_audio(audio_path, detected_lang)
        logger.info(f"Transcribed text (regional): '{regional_text}'")
    else:
        regional_text = input_text
        logger.info(f"Using input text as regional text: '{regional_text}'")

    logger.info(f"Translating from {detected_lang} to English...")
    english_input = translate_to_english(regional_text, lang_code)
    logger.info(f"Translated to English: '{english_input}'")
    
    chat_history.append({"role": "user", "content": english_input})
    logger.info(f"Sending translated prompt to GPT: '{english_input}'")
    reply_english = get_gpt_response(chat_history)
    logger.info(f"GPT response in English: '{reply_english}'")
    
    chat_history.append({"role": "assistant", "content": reply_english})
    logger.info(f"Translating GPT response back to {detected_lang}...")
    reply_regional = translate_back(reply_english, lang_code)
    logger.info(f"Translated response: '{reply_regional}'")

    logger.info("Synthesizing audio response...")
    audio_path = synthesize_and_save_audio(reply_regional, lang_code)
    audio_url = f"http://localhost:8000{audio_path}"
    logger.info(f"Audio response saved at: {audio_url}")

    response_data = {
        "tool": req.tool,
        "type": req.type,
        "input": {
            "text": regional_text,
            "audio_url": input_data.audio_url,
            "target_lang": lang_code,
            "detected_lang": detected_lang,
            "english_input": english_input,
            "translated_text": reply_regional,
            "audio_response_path": audio_url
        }
    }
    logger.info(f"Translation process completed successfully for {detected_lang} input")
    logger.debug(f"Returning response: {response_data}")
    return response_data
