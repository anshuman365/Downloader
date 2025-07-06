import threading
import queue
import json
import os
import shutil
import time
import logging
from datetime import datetime
from config import Config
from .downloader import download_media
from .search import search_youtube
from .utils import sanitize_filename  # Import sanitize function

# Task queue and worker threads
task_queue = queue.Queue()
workers = []

def get_user_db(user_id):
    db_file = os.path.join(Config.USERS_DIR, user_id, 'database.json')
    try:
        if os.path.exists(db_file):
            # Handle empty file case
            if os.path.getsize(db_file) == 0:
                return {"queue": [], "history": []}
                
            with open(db_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading user database: {e}")
    return {"queue": [], "history": []}

def save_user_db(user_id, data):
    db_file = os.path.join(Config.USERS_DIR, user_id, 'database.json')
    try:
        with open(db_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving user database: {e}")

def get_queue(user_id):
    return get_user_db(user_id).get("queue", [])

def get_history(user_id):
    return get_user_db(user_id).get("history", [])

def add_to_queue(user_id, task):
    task['id'] = f"task-{int(time.time() * 1000)}"
    data = get_user_db(user_id)
    
    # Ensure task is a dictionary before saving
    if isinstance(task, dict):
        data["queue"].append(task)
    else:
        logging.error(f"Invalid task type: {type(task)}")
        return None
        
    save_user_db(user_id, data)
    return task

def remove_from_queue(user_id, task_id):
    data = get_user_db(user_id)
    if "queue" in data:
        data["queue"] = [t for t in data["queue"] if isinstance(t, dict) and t.get('id') != task_id]
        save_user_db(user_id, data)

def update_task_status(user_id, task_id, status, error=None):
    data = get_user_db(user_id)
    
    # Ensure queue exists and is a list
    if "queue" not in data:
        data["queue"] = []
    
    for task in data["queue"]:
        # Ensure task is a dictionary and has matching ID
        if isinstance(task, dict) and task.get('id') == task_id:
            task["status"] = status
            if error:
                task["error"] = str(error)
            break
    else:
        logging.warning(f"Task {task_id} not found in queue for user {user_id}")
    
    save_user_db(user_id, data)

def add_to_history(user_id, task):
    data = get_user_db(user_id)
    if "history" not in data:
        data["history"] = []
    data["history"].append(task)
    save_user_db(user_id, data)

def find_existing_file(url, is_audio, quality):
    for user_dir in os.listdir(Config.USERS_DIR):
        downloads_dir = os.path.join(Config.USERS_DIR, user_dir, 'downloads')
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                if url in file:
                    return os.path.join(downloads_dir, file)
    return None

def copy_file_to_user(user_id, source_file):
    user_downloads = os.path.join(Config.USERS_DIR, user_id, 'downloads')
    os.makedirs(user_downloads, exist_ok=True)
    filename = os.path.basename(source_file)
    
    # Sanitize filename before copying
    sanitized_name = sanitize_filename(filename)
    dest_file = os.path.join(user_downloads, sanitized_name)
    
    # Only copy if sanitization changed the name
    if filename != sanitized_name:
        shutil.copy2(source_file, dest_file)
        logging.info(f"Copied and sanitized: {filename} -> {sanitized_name}")
        return sanitized_name
    else:
        # If no change needed, copy with original name
        shutil.copy2(source_file, os.path.join(user_downloads, filename))
        return filename

# Update the worker function
def worker():
    while True:
        task = task_queue.get()
        try:
            # Ensure task is a dictionary
            if not isinstance(task, dict):
                logging.error(f"Invalid task type: {type(task)}")
                continue
                
            user_id = task.get('user_id')
            if not user_id:
                logging.error("Task missing user_id")
                continue

            task_id = task.get('id', '')
            if not task_id:
                logging.error("Task missing ID")
                continue
                
            # Check if task was paused
            current_status = get_task_status(user_id, task_id)
            if current_status == "paused":
                logging.info(f"Task {task_id} is paused, skipping")
                task_queue.task_done()
                continue
                
            # Update status before processing
            update_task_status(user_id, task_id, "processing")
            
            # Extract input string first
            input_str = task.get('input', '')
            if not input_str:
                raise ValueError("Task missing input")
                
            # Extract URL from input
            if input_str.startswith(('http://', 'https://')):
                url = input_str
            elif "youtube.com" in input_str or "youtu.be" in input_str:
                url = input_str
            else:
                url = search_youtube(input_str)
                if not url:
                    raise ValueError("No search results found")

            # Determine media type and quality
            is_audio = task.get('media_type', 'audio') == 'audio'
            quality = task.get('quality', '')
            if is_audio:
                quality_val = quality if quality in Config.AUDIO_QUALITIES else Config.DEFAULT_AUDIO_QUALITY
            else:
                quality_val = quality if quality in Config.VIDEO_QUALITIES else Config.DEFAULT_VIDEO_QUALITY

            def progress_callback(d):
                if d['status'] == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    if total and total > 0:
                        progress = int((downloaded / total) * 100)
                        update_task_progress(user_id, task_id, progress)
            
            # Check for existing file
            existing_file = find_existing_file(url, is_audio, quality_val)
            if existing_file:
                filename = copy_file_to_user(user_id, existing_file)
                update_task_progress(user_id, task_id, 100)
            else:
                filename = download_media(url, is_audio, quality_val, user_id, progress_callback)
                update_task_progress(user_id, task_id, 100)

            if not filename:
                raise ValueError("Download failed")

            # Create completed task record
            completed_task = {
                "id": task_id,
                "input": input_str,
                "url": url,
                "file": filename,
                "type": "audio" if is_audio else "video",
                "quality": quality or 'default',
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            # Update history and queue
            add_to_history(user_id, completed_task)
            remove_from_queue(user_id, task_id)
            logging.info(f"[{user_id}] Task completed: {input_str} -> {filename}")

        except Exception as e:
            logging.error(f"Task failed: {str(e)}")
            logging.debug(f"Failed task details: {task}")
            
            # Update status with error if we have required identifiers
            if user_id and task_id:
                update_task_status(user_id, task_id, "failed", str(e))
        finally:
            task_queue.task_done()

def start_workers():
    global workers
    if not workers:
        for _ in range(Config.MAX_WORKERS):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            workers.append(t)
        logging.info(f"Started {Config.MAX_WORKERS} worker threads")

def add_task_to_queue(task):
    user_id = task.get('user_id')
    if not user_id:
        raise ValueError("Missing user_id in task")
    db_task = add_to_queue(user_id, task)
    task_queue.put(db_task)
    return db_task

# Add these functions to queue_manager.py
def pause_task(user_id, task_id):
    data = get_user_db(user_id)
    for task in data["queue"]:
        if task.get('id') == task_id:
            if task["status"] == "processing":
                task["status"] = "paused"
                save_user_db(user_id, data)
                return True
    return False

def resume_task(user_id, task_id):
    data = get_user_db(user_id)
    for task in data["queue"]:
        if task.get('id') == task_id and task["status"] == "paused":
            task["status"] = "queued"
            save_user_db(user_id, data)
            # Re-add to processing queue
            task_queue.put(task)
            return True
    return False

def delete_task(user_id, task_id):
    data = get_user_db(user_id)
    task_to_delete = None
    
    # Find task in queue
    for task in data["queue"]:
        if task.get('id') == task_id:
            task_to_delete = task
            break
            
    if task_to_delete:
        # Clean up partial files
        if task_to_delete.get('file'):
            user_downloads = os.path.join(Config.USERS_DIR, user_id, 'downloads')
            partial_files = [f for f in os.listdir(user_downloads) 
                           if f.startswith(task_to_delete['file'].split('.')[0])]
            for file in partial_files:
                try:
                    os.remove(os.path.join(user_downloads, file))
                    logging.info(f"Deleted partial file: {file}")
                except Exception as e:
                    logging.error(f"Error deleting partial file: {e}")
        
        data["queue"] = [t for t in data["queue"] if t.get('id') != task_id]
        save_user_db(user_id, data)
        return True
    return False

def update_task_progress(user_id, task_id, progress):
    data = get_user_db(user_id)
    for task in data["queue"]:
        if isinstance(task, dict) and task.get('id') == task_id:
            task["progress"] = progress
            break
    save_user_db(user_id, data)
    
# Add this helper function
def get_task_status(user_id, task_id):
    data = get_user_db(user_id)
    for task in data["queue"]:
        if task.get('id') == task_id:
            return task.get('status')
    return None