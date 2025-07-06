from flask import Flask, g, url_for, redirect
from config import Config
from .utils import setup_logging, get_current_user
import os
import logging

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = 'your_secret_key_here'
    
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    sessions_dir = os.path.join(Config.USERS_DIR, '../sessions')
    os.makedirs(sessions_dir, exist_ok=True)

    # Add this to create_app()
    app.config['UPLOADS_DIR'] = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(app.config['UPLOADS_DIR'], exist_ok=True)
    
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    from .routes import main_bp
    from .auth_routes import auth_bp
    from .user_routes import user_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    
    # Register template filters
    from .utils import format_time_filter
    app.template_filter('format_time')(format_time_filter)
    
    from .routes import index
    @app.route('/')
    def home():
        return redirect(url_for('main.index'))
    
    # Context processor for global template variables
    @app.context_processor
    def inject_user():
        user = get_current_user()
        if user:
            # Only return safe fields
            return dict(
                username=user['username'],
                user={
                    'id': user['id'],
                    'username': user['username'],
                    'email': user.get('email', ''),
                    'profile_pic': user.get('profile_pic', ''),
                    'default_audio_quality': user.get('default_audio_quality', Config.DEFAULT_AUDIO_QUALITY),
                    'default_video_quality': user.get('default_video_quality', Config.DEFAULT_VIDEO_QUALITY)
                }
            )
        return dict(username=None, user=None)
    
    # Start workers
    from .queue_manager import start_workers
    start_workers()
    
    # Create users directory if not exists
    os.makedirs(Config.USERS_DIR, exist_ok=True)
    
    return app

