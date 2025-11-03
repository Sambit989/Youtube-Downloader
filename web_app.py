from flask import Flask, render_template, request, send_from_directory
import subprocess
import os
import re
from datetime import datetime
import urllib.parse

app = Flask(__name__)

# Configuration
DOWNLOAD_VIDEO_DIR = os.path.join('downloads', 'youtube_videos')
DOWNLOAD_AUDIO_DIR = os.path.join('downloads', 'youtube_audio')
MAX_RETRIES = 3  # Maximum number of retry attempts
SUPPORTED_RESOLUTIONS = {
    '1': {'name': '1080p', 'height': '1080', 'description': 'Full HD'},
    '2': {'name': '720p', 'height': '720', 'description': 'HD'},
    '3': {'name': '480p', 'height': '480', 'description': 'Standard'},
    '4': {'name': '360p', 'height': '360', 'description': 'Low'},
}

# Ensure download directories exist
for directory in [DOWNLOAD_VIDEO_DIR, DOWNLOAD_AUDIO_DIR]:
    os.makedirs(directory, exist_ok=True)

# Utility functions
def validate_youtube_url(url):
    """Validate YouTube URL format."""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube\.com/watch\?v=|youtu\.be/)'
        '[A-Za-z0-9_-]{11}'
    )
    return bool(re.match(youtube_regex, url))


def list_recent_downloads(limit=8):
    """Return a list of recent downloaded files (videos and audio)."""
    entries = []
    for kind, d in (('video', DOWNLOAD_VIDEO_DIR), ('audio', DOWNLOAD_AUDIO_DIR)):
        try:
            for fn in os.listdir(d):
                path = os.path.join(d, fn)
                if os.path.isfile(path):
                    entries.append({
                        'kind': kind,
                        'name': fn,
                        'path': path,
                        'mtime': os.path.getmtime(path),
                        'size': os.path.getsize(path),
                    })
        except FileNotFoundError:
            continue

    entries.sort(key=lambda e: e['mtime'], reverse=True)

    def _human_size(n):
        # simple human-readable size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if n < 1024.0:
                return f"{n:3.1f} {unit}"
            n /= 1024.0
        return f"{n:.1f} PB"

    # Convert mtime to readable, size, and build URL (URL-encoded)
    for e in entries:
        e['mtime_readable'] = datetime.fromtimestamp(e['mtime']).strftime('%Y-%m-%d %H:%M:%S')
        e['size_readable'] = _human_size(e.get('size', 0))
        e['url'] = f"/files/{e['kind']}/{urllib.parse.quote(e['name'])}"

    return entries[:limit]


def most_recent_file_in_dir(directory, after_ts=0):
    """Return the most recent filename in `directory` with mtime >= after_ts, or None."""
    best = None
    try:
        for fn in os.listdir(directory):
            path = os.path.join(directory, fn)
            if os.path.isfile(path):
                m = os.path.getmtime(path)
                if m >= after_ts and (best is None or m > best[0]):
                    best = (m, fn)
    except FileNotFoundError:
        return None
    return best[1] if best else None


@app.route('/', methods=['GET'])
def index():
    """Render the main page with resolution presets."""
    return render_template('index.html', resolutions=SUPPORTED_RESOLUTIONS)


@app.route('/download', methods=['POST'])
def download():
    """Handle download requests for YouTube videos/audio."""
    url = request.form.get('url', '').strip()
    kind = request.form.get('kind', 'mp4')
    resolution = request.form.get('resolution', '').strip()

    # Validate input
    if not url:
        return render_template('index.html', 
                             error='Please provide a YouTube URL.',
                             resolutions=SUPPORTED_RESOLUTIONS)
    
    if not validate_youtube_url(url):
        return render_template('index.html',
                             error='Invalid YouTube URL. Please provide a valid YouTube video URL.',
                             resolutions=SUPPORTED_RESOLUTIONS)
                             
    # Track start time for download duration
    start_time = datetime.now()

    if not url:
        return render_template('index.html', error='Please provide a YouTube URL.')

    # Build command similar to app.py logic
    if kind == 'mp3':
        cmd = ['yt-dlp', '-x', '--audio-format', 'mp3', '-o', os.path.join(DOWNLOAD_AUDIO_DIR, '%(title)s.%(ext)s'), url]
    else:
        # resolution can be preset (1024,720,360) or custom like '480' or '1024,720' or '1024x720'
        width = None
        height = None
        if resolution in ('1', '1024'):
            height = '1024'
        elif resolution in ('3', '360'):
            height = '360'
        elif resolution in ('2', '720', ''):
            height = '720'
        else:
            r = resolution
            if ',' in r:
                parts = r.split(',')
                if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                    width, height = parts[0].strip(), parts[1].strip()
            elif 'x' in r.lower():
                parts = r.lower().split('x')
                if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                    width, height = parts[0].strip(), parts[1].strip()
            elif r.isdigit():
                height = r
            if not height:
                height = '720'

        filters = []
        if width:
            filters.append(f"width<={width}")
        if height:
            filters.append(f"height<={height}")
        filter_str = ''.join([f'[{f}]' for f in filters])
        fmt = f"bestvideo{filter_str}+bestaudio/best{filter_str}/best"
        cmd = ['yt-dlp', '-f', fmt, '--merge-output-format', 'mp4', '-o', os.path.join(DOWNLOAD_VIDEO_DIR, '%(title)s.%(ext)s'), url]

    # Run yt-dlp and capture output
    def run_cmd(c):
        try:
            p = subprocess.run(c, capture_output=True, text=True)
            return p.returncode == 0, p.stdout or '', p.stderr or ''
        except Exception as e:
            return False, '', str(e)

    success, output, error = run_cmd(cmd)
    attempts = [{'success': success}]

    # Detect common yt-dlp YouTube issues and try automatic fallbacks
    fallback_triggers = ['Signature extraction failed', 'Some web client https formats have been skipped', 'Some web_safari client https formats have been skipped', 'YouTube is forcing SABR streaming']
    needs_fallback = (not success) and any(t in (error + output) for t in fallback_triggers)

    if needs_fallback:
        # Try fallback methods quietly
        fallbacks = [
            ['--extractor-args', 'youtube:player_client=android'],
            ['--hls-prefer-ffmpeg'],
            ['--allow-unplayable-formats'],
        ]

        for opts in fallbacks:
            new_cmd = [cmd[0]] + opts + cmd[1:]
            s, out, err = run_cmd(new_cmd)
            if s:
                success = True
                attempts = [{'success': True}]
                break

    # Calculate download duration
    duration = (datetime.now() - start_time).total_seconds()
    
    # Prepare status message
    status_message = None
    if success:
        status_message = {
            'type': 'success',
            'message': f'Download completed successfully in {duration:.1f} seconds!'
        }
    elif needs_fallback and not success:
        status_message = {
            'type': 'warning',
            'message': 'Initial download failed. Tried alternative methods but could not complete the download. Please try updating yt-dlp using "pip install -U yt-dlp".'
        }
    else:
        status_message = {
            'type': 'error',
            'message': 'Download failed. Please check the error messages below.'
        }

    # Find recent downloads and the file created by this run (if any)
    recent = list_recent_downloads()
    downloaded_link = None
    after_ts = start_time.timestamp()
    latest = None
    if kind == 'mp3':
        latest = most_recent_file_in_dir(DOWNLOAD_AUDIO_DIR, after_ts)
        if latest:
            downloaded_link = f"/files/audio/{urllib.parse.quote(latest)}"
            latest_dir = DOWNLOAD_AUDIO_DIR
            latest_kind = 'audio'
    else:
        latest = most_recent_file_in_dir(DOWNLOAD_VIDEO_DIR, after_ts)
        if latest:
            downloaded_link = f"/files/video/{urllib.parse.quote(latest)}"
            latest_dir = DOWNLOAD_VIDEO_DIR
            latest_kind = 'video'

    # If user asked to stream (prompt browser save) and we have the downloaded filename, send it as attachment
    if request.form.get('stream') and latest:
        # send_from_directory will set Content-Disposition and prompt Save As in the browser
        return send_from_directory(latest_dir, latest, as_attachment=True)

    # Final template render includes all attempts and metadata
    return render_template('index.html',
                         success=success,
                         output=output,
                         error=error,
                         cmd=' '.join(cmd),
                         attempts=attempts,
                         status=status_message,
                         duration=duration,
                         resolutions=SUPPORTED_RESOLUTIONS,
                         recent_downloads=recent,
                         downloaded_link=downloaded_link)



@app.route('/files/<kind>/<path:filename>')
def serve_file(kind, filename):
    """Serve downloaded files (video/audio).

    kind: 'video' or 'audio'
    """
    if kind == 'video':
        directory = DOWNLOAD_VIDEO_DIR
    elif kind == 'audio':
        directory = DOWNLOAD_AUDIO_DIR
    else:
        return "Invalid file type", 400

    # Security note: send_from_directory will prevent path traversal
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    # Check yt-dlp version on startup
    try:
        version_check = subprocess.run(['yt-dlp', '--version'], 
                                     capture_output=True, 
                                     text=True)
        if version_check.returncode == 0:
            print(f"yt-dlp version: {version_check.stdout.strip()}")
        else:
            print("Warning: Could not determine yt-dlp version")
    except FileNotFoundError:
        print("Error: yt-dlp not found. Please install it using 'pip install yt-dlp'")
        exit(1)

    # Start the Flask application
    print("Starting YouTube Downloader Web App...")
    app.run(host='0.0.0.0', port=5000, debug=True)
