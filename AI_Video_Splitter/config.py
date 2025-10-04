import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-123')
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024 * 1024  # 1GB
    UPLOAD_FOLDER = 'uploads'
    TEMP_FOLDER = 'temp'
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}