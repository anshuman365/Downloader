import yt_dlp
from config import Config
import os
import logging
from .utils import sanitize_filename  # Import the sanitize function

def download_media(url, is_audio=True, quality=None, user_id=None, progress_callback=None):
    try:
        # Create user-specific downloads directory
        user_downloads = os.path.join(Config.USERS_DIR, user_id, 'downloads')
        os.makedirs(user_downloads, exist_ok=True)
        
        # Base template before sanitization
        base_template = os.path.join(user_downloads, '%(title)s.%(ext)s')
        
        # Add quality to filename template
        if quality:
            if is_audio:
                base_template = os.path.join(user_downloads, f'%(title)s_{quality}k.%(ext)s')
            else:
                base_template = os.path.join(user_downloads, f'%(title)s_{quality}p.%(ext)s')
        
        opts = {
            'outtmpl': base_template,
            'quiet': True,
            'no_warnings': True,
            'logger': logging.getLogger(),
            'progress_hooks': [progress_callback] if progress_callback else [],
            'noprogress': False,
        }

        if is_audio:
            bitrate = quality or Config.DEFAULT_AUDIO_QUALITY
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': Config.DEFAULT_AUDIO_FORMAT,
                    'preferredquality': bitrate,
                }]
            })
        else:
            height = quality or Config.DEFAULT_VIDEO_QUALITY
            opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
            opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if is_audio:
                base, _ = os.path.splitext(filename)
                filename = f"{base}.{Config.DEFAULT_AUDIO_FORMAT}"
            
            # Sanitize the final filename
            sanitized_name = sanitize_filename(os.path.basename(filename))
            sanitized_path = os.path.join(user_downloads, sanitized_name)
            
            # Rename if sanitization changed the filename
            if os.path.basename(filename) != sanitized_name:
                os.rename(
                    os.path.join(user_downloads, os.path.basename(filename)),
                    sanitized_path
                )
                logging.info(f"Sanitized filename: {os.path.basename(filename)} -> {sanitized_name}")
            
            return sanitized_name
            
    except Exception as e:
        logging.error(f"Download failed for {url}: {e}")
        # Return partial filename if exists
        if 'filename' in locals():
            return os.path.basename(filename)
        return None