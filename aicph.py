
import cv2
import face_recognition
import pytesseract
from PIL import Image
from sentence_transformers import SentenceTransformer, util
#most stuff is free to implement, install libs with requirements1.txt
#consent form has 2 signatures, required signature is within blackbounded box. returns positions of the signature/fingerprint as a box. I dont know
#what to do with the box after that.
def detect_signature_position(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    positions = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 100]
    return positions

#Face match of two images. Returns true/false. 
def compare_faces(base_image_path, compare_image_path):
    base_image = face_recognition.load_image_file(base_image_path)
    compare_image = face_recognition.load_image_file(compare_image_path)
    base_encoding = face_recognition.face_encodings(base_image)[0]
    compare_encoding = face_recognition.face_encodings(compare_image)[0]
    results = face_recognition.compare_faces([base_encoding], compare_encoding)
    return results[0]

#Simple OCR function. But it pulls from the entire image. returns string.
def extract_text(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    return text.strip()

#Similarity check for without LLM but with emeddings used in typical GPT etc. Should be lightweight
model = SentenceTransformer('all-MiniLM-L6-v2')

def compare_text_similarity(text1, text2, threshold=0.7):
    embeddings = model.encode([text1, text2], convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
    return similarity >= threshold
