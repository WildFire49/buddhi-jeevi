import pytesseract
from PIL import Image
import difflib

def extract_text(image_path: str) -> str:
    """
    Extracts text from an image using pytesseract.
    """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip()

def match_text_from_image(image_path: str, expected_text: str, threshold: float = 0.16) -> dict:
    """
    Compares extracted OCR text from the image with an expected string.

    Args:
        image_path (str): Path to the image.
        expected_text (str): The text you expect to be in the image (e.g., name).
        threshold (float): Match threshold for similarity (0-1).

    Returns:
        dict: OCR text, match score, and match status.
    """
    ocr_text = extract_text(image_path)

    # Normalize
    ocr_clean = ocr_text.lower().replace("\n", " ").strip()
    expected_clean = expected_text.lower().strip()

    similarity = difflib.SequenceMatcher(None, ocr_clean, expected_clean).ratio()

    return {
        "ocr_text": ocr_text,
        "expected_text": expected_text,
        "similarity_score": round(similarity, 3),
        "match": similarity >= threshold
    }
