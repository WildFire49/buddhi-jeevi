import os
import tempfile
import logging
from typing import Dict, Any, Optional
from storage.minio_service import MinioService
from multimedia.ocr import extract_text, match_text_from_image

logger = logging.getLogger(__name__)

class OCRService:
    """Service for performing OCR on images stored in MinIO"""
    
    def __init__(self):
        """Initialize OCR service with MinIO client"""
        self.minio_service = MinioService()
        logger.info("OCR Service initialized")
    
    def process_image(self, object_id: str) -> Dict[str, Any]:
        """
        Process an image from MinIO with OCR
        
        Args:
            object_id: The MinIO object ID of the image
            
        Returns:
            Dict: OCR results containing extracted text and status
        """
        try:
            # Get the image URL from MinIO
            image_url = self.minio_service.get_file_url(object_id)
            
            if not image_url:
                logger.error(f"Image with ID {object_id} not found in MinIO")
                return {
                    "success": False,
                    "error": "Image not found",
                    "object_id": object_id
                }
            
            # Download the image to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_path = temp_file.name
                
                # Use requests to download the image
                import requests
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                else:
                    logger.error(f"Failed to download image: HTTP {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Failed to download image: HTTP {response.status_code}",
                        "object_id": object_id
                    }
            
            # Extract text from the image
            try:
                extracted_text = extract_text(temp_path)
                
                # Clean up the temporary file
                os.unlink(temp_path)
                
                return {
                    "success": True,
                    "object_id": object_id,
                    "text": extracted_text,
                    "image_url": image_url
                }
                
            except Exception as e:
                logger.error(f"OCR processing error: {str(e)}")
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
                return {
                    "success": False,
                    "error": f"OCR processing error: {str(e)}",
                    "object_id": object_id
                }
                
        except Exception as e:
            logger.error(f"Error processing image with ID {object_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "object_id": object_id
            }
    
    def match_text(self, object_id: str, expected_text: str, threshold: float = 0.16) -> Dict[str, Any]:
        """
        Match expected text against OCR results from an image
        
        Args:
            object_id: The MinIO object ID of the image
            expected_text: The text to match against the OCR result
            threshold: Similarity threshold (0-1)
            
        Returns:
            Dict: Match results with similarity score and status
        """
        try:
            # Get the image URL from MinIO
            image_url = self.minio_service.get_file_url(object_id)
            
            if not image_url:
                logger.error(f"Image with ID {object_id} not found in MinIO")
                return {
                    "success": False,
                    "error": "Image not found",
                    "object_id": object_id
                }
            
            # Download the image to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_path = temp_file.name
                
                # Use requests to download the image
                import requests
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                else:
                    logger.error(f"Failed to download image: HTTP {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Failed to download image: HTTP {response.status_code}",
                        "object_id": object_id
                    }
            
            # Match text from the image
            try:
                match_result = match_text_from_image(temp_path, expected_text, threshold)
                
                # Clean up the temporary file
                os.unlink(temp_path)
                
                return {
                    "success": True,
                    "object_id": object_id,
                    "image_url": image_url,
                    "match_result": match_result
                }
                
            except Exception as e:
                logger.error(f"Text matching error: {str(e)}")
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
                return {
                    "success": False,
                    "error": f"Text matching error: {str(e)}",
                    "object_id": object_id
                }
                
        except Exception as e:
            logger.error(f"Error matching text for image with ID {object_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "object_id": object_id
            }
