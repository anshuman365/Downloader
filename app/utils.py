from flask import request, current_app
from config import Config
from .auth import validate_session, get_user
import logging
from datetime import datetime
import os
import json
import re

def get_current_user():
    session_id = request.cookies.get(Config.SESSION_COOKIE_NAME)
    if not session_id or not validate_session(session_id):
        return None
    
    # Get user from session
    sessions_dir = os.path.join(Config.USERS_DIR, '../sessions')
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    
    with open(session_file) as f:
        session_data = json.load(f)
    
    return get_user(session_data['user_id'])

def setup_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def format_time_filter(s):
    dt = datetime.fromisoformat(s)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Add sanitize_filename function here
def sanitize_filename(filename):
    """
    Sanitize filenames by replacing problematic characters
    """
    # Replace full-width characters with standard equivalents
    replacements = {
        '：': '_',  # Full-width colon
        '｜': '_',  # Full-width vertical bar
        '：': ':',  # Normal colon
        ' ': '_',   # Space
        '/': '_',   # Slash
        '\\': '_',  # Backslash
        ':': '_',   # Colon
        '*': '_',   # Asterisk
        '?': '_',   # Question mark
        '"': '_',   # Double quote
        '<': '_',   # Less than
        '>': '_',   # Greater than
        '|': '_',   # Pipe
    }
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    
    # Remove any remaining non-ASCII characters
    filename = re.sub(r'[^\x00-\x7F]+', '_', filename)
    return filename

def get_actual_filepath(directory, filename):
    """Get actual file path with correct case"""
    # First check if the file exists with the exact case
    exact_path = os.path.join(directory, filename)
    if os.path.exists(exact_path):
        return exact_path
    
    # Find case-insensitive match
    files = os.listdir(directory)
    actual_filename = next((f for f in files if f.lower() == filename.lower()), None)
    
    if actual_filename:
        return os.path.join(directory, actual_filename)
    
    return None