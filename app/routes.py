from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, jsonify, g, current_app, flash, send_file
from .decorators import login_required
from .queue_manager import add_task_to_queue, get_queue, get_history
import app.queue_manager as queue_manager
from .search import search_youtube_multiple
import os
import logging
from datetime import datetime
import urllib.parse
from .utils import get_actual_filepath  # Add this import

main_bp = Blueprint('main', __name__, url_prefix='/main')

@main_bp.route('/')
@login_required
def index():
    user = g.user
    queue = get_queue(user['id'])
    history = get_history(user['id'])
    
    # Calculate user count
    user_count = len([name for name in os.listdir('data/users') 
                     if os.path.isdir(os.path.join('data/users', name))])
    
    # Calculate storage used (simplified)
    storage_used = "0 MB"  # Placeholder
    
    return render_template('index.html', 
                          queue_count=len(queue), 
                          history_count=len(history),
                          user_count=user_count,
                          user=user,
                          storage_used=storage_used)

@main_bp.route('/api/search')
def search_api():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = search_youtube_multiple(query, limit=5)
    return jsonify(results)

@main_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    user = g.user
    input_str = request.form['input'].strip()
    is_audio = request.form.get('media_type', 'audio') == 'audio'
    quality = request.form.get('quality', '')
    
    if not input_str:
        return redirect(url_for('main.index'))
    
    # Create proper task dictionary structure
    task = {
        'input': input_str,
        'media_type': 'audio' if is_audio else 'video',
        'quality': quality,
        'status': 'queued',
        'timestamp': datetime.now().isoformat(),
        'user_id': user['id'],
        'progress': 0
    }
    
    add_task_to_queue(task)
    logging.info(f"Added task: {input_str} ({'audio' if is_audio else 'video'}) at quality {quality}")
    
    return redirect(url_for('main.queue'))

@main_bp.route('/queue')
@login_required
def queue():
    user = g.user
    tasks = get_queue(user['id'])
    
    # Ensure all tasks are dictionaries
    valid_tasks = []
    for task in tasks:
        if isinstance(task, dict):
            valid_tasks.append(task)
        else:
            logging.error(f"Invalid task in queue: {task}")
    
    return render_template('queue.html', tasks=valid_tasks)

@main_bp.route('/history')
@login_required
def history():
    user = g.user
    tasks = get_history(user['id'])
    
    # Ensure all tasks are dictionaries
    valid_tasks = []
    for task in tasks:
        if isinstance(task, dict):
            valid_tasks.append(task)
        else:
            logging.error(f"Invalid task in history: {task}")
    
    return render_template('history.html', tasks=valid_tasks)

# Add this new route for debugging
@main_bp.route('/debug/filepath/<path:filename>')
@login_required
def debug_filepath(filename):
    # Decode URL-encoded filename
    decoded_filename = urllib.parse.unquote(filename)
    
    # Get the user's downloads directory
    user_downloads = os.path.join(current_app.config['USERS_DIR'], g.user['id'], 'downloads')
    file_path = os.path.join(user_downloads, decoded_filename)
    
    # Check if file exists
    exists = os.path.exists(file_path)
    size = os.path.getsize(file_path) if exists else 0
    
    return jsonify({
        "requested_filename": filename,
        "decoded_filename": decoded_filename,
        "full_path": file_path,
        "exists": exists,
        "size": size
    })

# Update the download rout
@main_bp.route('/downloads/<path:filename>')
@login_required
def download_file(filename):
    # Decode URL-encoded filename
    decoded_filename = urllib.parse.unquote(filename)
    
    # Get the user's downloads directory using the correct base path
    project_root = os.path.dirname(current_app.root_path)
    users_dir = os.path.join(project_root, 'data', 'users')
    user_downloads = os.path.join(users_dir, g.user['id'], 'downloads')
    
    # Log for debugging
    logging.info(f"Download request: {filename}")
    logging.info(f"Decoded filename: {decoded_filename}")
    logging.info(f"Full path: {os.path.join(user_downloads, decoded_filename)}")
    logging.info(f"Files in directory: {os.listdir(user_downloads)}")
    
    # Get actual file path
    actual_path = get_actual_filepath(user_downloads, decoded_filename)
    
    if not actual_path or not os.path.exists(actual_path):
        logging.error(f"File not found: {decoded_filename}")
        abort(404)
    
    # Send the file as an attachment
    return send_file(actual_path, as_attachment=True)

# Add these routes to routes.py
@main_bp.route('/pause_task', methods=['POST'])
@login_required
def pause_task():
    user_id = g.user['id']
    task_id = request.form['task_id']
    if queue_manager.pause_task(user_id, task_id):
        flash('Task paused successfully', 'success')
    else:
        flash('Failed to pause task', 'error')
    return redirect(url_for('main.queue'))

@main_bp.route('/resume_task', methods=['POST'])
@login_required
def resume_task():
    user_id = g.user['id']
    task_id = request.form['task_id']
    if queue_manager.resume_task(user_id, task_id):
        flash('Task resumed successfully', 'success')
    else:
        flash('Failed to resume task', 'error')
    return redirect(url_for('main.queue'))

@main_bp.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
    user_id = g.user['id']
    task_id = request.form['task_id']
    if queue_manager.delete_task(user_id, task_id):
        flash('Task deleted successfully', 'success')
    else:
        flash('Failed to delete task', 'error')
    return redirect(url_for('main.queue'))

# Add to routes.py
@main_bp.route('/retry_task', methods=['POST'])
@login_required
def retry_task():
    task_id = request.form['task_id']
    user_id = g.user['id']
    
    # Find task in history
    history = get_history(user_id)
    task = next((t for t in history if t.get('id') == task_id), None)
    
    if task:
        # Clean up partial files
        if task.get('file'):
            base_name = task['file'].split('.')[0]
            cleanup_partial_files(user_id, base_name)
        
        # Reset task status
        task['status'] = 'queued'
        task['progress'] = 0
        task.pop('error', None)
        
        # Add back to queue
        add_task_to_queue(task)
        return jsonify(success=True)
    
    return jsonify(success=False, error="Task not found")