import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from config import Config

def create_user(username, password):
    user_id = str(uuid.uuid4())
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    
    user_dir = os.path.join(Config.USERS_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    user_data = {
        'id': user_id,
        'username': username,
        'password': key.hex(),
        'salt': salt.hex(),
        'created_at': datetime.now().isoformat(),
        'email': '',
        'profile_pic': '',
        'default_audio_quality': '128k',
        'default_video_quality': '720p'
    }
    
    with open(os.path.join(user_dir, 'profile.json'), 'w') as f:
        json.dump(user_data, f)
    
    with open(os.path.join(user_dir, 'database.json'), 'w') as f:
        json.dump({"queue": [], "history": []}, f)
    
    return user_data

def authenticate_user(username, password):
    for user_id in os.listdir(Config.USERS_DIR):
        profile_path = os.path.join(Config.USERS_DIR, user_id, 'profile.json')
        if os.path.exists(profile_path):
            with open(profile_path) as f:
                user_data = json.load(f)
                if user_data['username'] == username:
                    salt = bytes.fromhex(user_data['salt'])
                    key = hashlib.pbkdf2_hmac(
                        'sha256',
                        password.encode('utf-8'),
                        salt,
                        100000
                    )
                    if key.hex() == user_data['password']:
                        return user_data
    return None

def get_user(user_id):
    profile_path = os.path.join(Config.USERS_DIR, user_id, 'profile.json')
    if os.path.exists(profile_path):
        with open(profile_path) as f:
            return json.load(f)
    return None

def create_session(user_id):
    session_id = str(uuid.uuid4())
    expires_at = (datetime.now() + timedelta(days=30)).isoformat()
    
    session_data = {
        'session_id': session_id,
        'user_id': user_id,
        'expires_at': expires_at
    }
    
    # Store session
    sessions_dir = os.path.join(Config.USERS_DIR, '../sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    with open(os.path.join(sessions_dir, f"{session_id}.json"), 'w') as f:
        json.dump(session_data, f)
    
    return session_data

# Update validate_session function
def validate_session(session_id):
    sessions_dir = os.path.join(Config.USERS_DIR, '../sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    
    if not os.path.exists(session_file):
        return False
    
    with open(session_file) as f:
        session_data = json.load(f)
    
    if datetime.fromisoformat(session_data['expires_at']) < datetime.now():
        return False
    
    return True

# Add to auth.py
def update_user(user_id, **kwargs):
    profile_path = os.path.join(Config.USERS_DIR, user_id, 'profile.json')
    if not os.path.exists(profile_path):
        return False
    
    with open(profile_path, 'r') as f:
        user_data = json.load(f)
    
    # Handle password update - don't invalidate existing sessions
    if 'password' in kwargs:
        # Keep existing salt for current sessions
        salt = bytes.fromhex(user_data['salt'])
        key = hashlib.pbkdf2_hmac(
            'sha256',
            kwargs['password'].encode('utf-8'),
            salt,
            100000
        )
        user_data['password'] = key.hex()
        # Keep existing salt - don't generate new one
    
    # Update other fields
    for key, value in kwargs.items():
        if key != 'password':
            user_data[key] = value
    
    with open(profile_path, 'w') as f:
        json.dump(user_data, f)
    
    return True
