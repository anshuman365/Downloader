from youtubesearchpython import VideosSearch
import logging
import yt_dlp

def search_youtube(query):
    try:
        videos_search = VideosSearch(query, limit=1)
        result = videos_search.result()
        
        if result and 'result' in result and result['result']:
            return result['result'][0]['link']
        logging.warning(f"No results found for: {query}")
        return None
    except Exception as e:
        logging.error(f"Search failed for '{query}': {e}")
        return None

def search_youtube_multiple(query, limit=15):
    try:
        videos_search = VideosSearch(query, limit=limit)
        result = videos_search.result()
        
        if result and 'result' in result and result['result']:
            return [
                {
                    'title': item['title'],
                    'url': item['link'],
                    'duration': item.get('duration', ''),
                    'thumbnail': item['thumbnails'][0]['url'] if item.get('thumbnails') else ''
                }
                for item in result['result']
            ]
        logging.warning(f"No results found for: {query}")
        return []
    except Exception as e:
        logging.error(f"Search failed for '{query}': {e}")
        return []

def fallback_search_youtube(query, limit=15):
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(
                f"ytsearch{limit}:{query}",
                download=False
            )
            
            if not result or 'entries' not in result:
                return []
                
            return [
                {
                    'title': entry.get('title', ''),
                    'url': entry.get('url', ''),
                    'duration': entry.get('duration', ''),
                    'thumbnail': entry.get('thumbnail', '')
                }
                for entry in result['entries']
            ]
            
    except Exception as e:
        logging.error(f"Fallback search failed: {e}")
        return []