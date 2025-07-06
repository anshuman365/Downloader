from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from .auth import update_user, get_user
from .decorators import login_required
import os
import logging
from config import Config

user_bp = Blueprint('user', __name__)

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    try:
        user = get_user(g.user['id'])
    
        if request.method == 'POST':
            # Handle profile updates
            updates = {}
            if 'email' in request.form:
                updates['email'] = request.form['email']
            if 'new_password' in request.form and request.form['new_password']:
                updates['password'] = request.form['new_password']
        
            # Handle profile picture upload
            if 'profile_pic' in request.files:
                profile_pic = request.files['profile_pic']
                if profile_pic.filename != '':
                    filename = f"user_{user['id']}.jpg"
                    profile_pic.save(os.path.join(Config.UPLOADS_DIR, filename))
                    updates['profile_pic'] = filename
        
            # Handle quality settings
            if 'default_audio_quality' in request.form:
                updates['default_audio_quality'] = request.form['default_audio_quality']
            if 'default_video_quality' in request.form:
                updates['default_video_quality'] = request.form['default_video_quality']
        
            if update_user(user['id'], **updates):
                flash('Settings updated successfully!', 'success')
            else:
                flash('Failed to update settings', 'error')
        
            return redirect(url_for('user.settings'))
    
        return render_template('settings.html', user=user, 
                              audio_qualities=Config.AUDIO_QUALITIES,
                              video_qualities=Config.VIDEO_QUALITIES)
                                  
    except Exception as e:
        logging.error(f"Error in settings: {e}")
        flash("An error occurred while loading settings", "error")
        return redirect(url_for('main.index'))