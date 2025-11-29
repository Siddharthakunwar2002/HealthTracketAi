import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # MongoDB settings
    MONGODB_HOST = os.environ.get('MONGODB_HOST') or 'localhost'
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT') or 27017)
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'healthcare_system'
    MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME')
    MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')
    
    # Construct MongoDB URI
    if MONGODB_USERNAME and MONGODB_PASSWORD:
        MONGODB_URI = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}"
    else:
        MONGODB_URI = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}"
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # WebRTC settings
    TURN_SERVER_URL = os.environ.get('TURN_SERVER_URL') or 'turn:turn.example.com:3478'
    TURN_USERNAME = os.environ.get('TURN_USERNAME') or ''
    TURN_PASSWORD = os.environ.get('TURN_PASSWORD') or ''
    STUN_SERVER_URL = os.environ.get('STUN_SERVER_URL') or 'stun:stun.l.google.com:19302'
    
    # Call settings
    MAX_CALL_DURATION = int(os.environ.get('MAX_CALL_DURATION') or 3600)  # 1 hour in seconds
    MAX_GROUP_PARTICIPANTS = int(os.environ.get('MAX_GROUP_PARTICIPANTS') or 10)
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Pagination
    POSTS_PER_PAGE = 10
    
    # Chat settings
    CHAT_HISTORY_LIMIT = 100
