from storage.minio_service import MinioService
import os
import mimetypes

def upload_image_to_minio(image_path, object_name=None):
    """Upload an image to MinIO and return the object ID"""
    # Initialize MinIO service
    minio_service = MinioService()
    
    # If no object name is provided, use the filename
    if not object_name:
        object_name = os.path.basename(image_path)
    
    # Get the content type
    content_type, _ = mimetypes.guess_type(image_path)
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Read the file data
    with open(image_path, 'rb') as file:
        file_data = file.read()
    
    # Upload the file
    print(f'Uploading {image_path} to MinIO bucket as {object_name}...')
    object_id = minio_service.upload_file(file_data, object_name, content_type)
    print(f'Upload successful! Object ID: {object_id}')
    return object_id

if __name__ == "__main__":
    # Upload the Aadhar card image
    image_path = '/home/devansh/Downloads/aadhar-card.jpg'
    if os.path.exists(image_path):
        object_id = upload_image_to_minio(image_path)
    else:
        print(f'Error: File {image_path} not found')
