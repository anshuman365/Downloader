import os
import logging 

class Config:
    # Application settings
    DOWNLOAD_DIR = 'downloads'
    DB_FILE = 'data/database.json'
    LOG_FILE = 'app.log'
    LOG_LEVEL = logging.DEBUG
    
    # YouTube settings
    DEFAULT_AUDIO_FORMAT = 'mp3'
    DEFAULT_VIDEO_FORMAT = 'mp4'

    # User settings
    USERS_DIR = 'data/users'
    UPLOADS_DIR = 'app/static/uploads'  # Added for profile pictures
    SESSION_COOKIE_NAME = 'ytdownloader_session'

    # Threading settings
    MAX_WORKERS = 3
    
    # Quality settings
    AUDIO_QUALITIES = ['64k', '128k', '192k', '256k', '320k']  # Updated to list
    VIDEO_QUALITIES = ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']  # Updated to list
    
    # Default qualities
    DEFAULT_AUDIO_QUALITY = '192k'  # Updated to match quality string
    DEFAULT_VIDEO_QUALITY = '720p'  # Updated to match quality string
    
    # Create required directories
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    os.makedirs(USERS_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)  # Added for profile pictures