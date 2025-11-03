# YouTube Downloader Web App

A simple and user-friendly web application built with Flask that allows you to download YouTube videos and extract audio directly from your browser. No registration required, fast downloads, and supports multiple formats and resolutions.

## Features

- **Video Downloads**: Download YouTube videos in high-quality MP4 format up to 1080p resolution
- **Audio Extraction**: Extract audio from YouTube videos as MP3 files
- **Web-Based Interface**: Clean, responsive UI with Tailwind CSS styling
- **Thumbnail Preview**: See video thumbnails before downloading
- **Recent Downloads**: View and access your last 10 downloads
- **Automatic Fallbacks**: Handles common YouTube download issues with retry mechanisms
- **No Installation Needed**: Works directly in your browser
- **Fast and Free**: Optimized for speed with no ads or registration

## Installation

### Prerequisites
- Python 3.6 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone the repository** (if applicable) or download the project files:
   ```bash
   git clone <repository-url>
   cd youtube-downloader-web-app
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install yt-dlp** (required for downloading):
   ```bash
   pip install yt-dlp
   ```

4. **Run the application**:
   ```bash
   python web_app.py
   ```

5. **Open your browser** and navigate to `http://localhost:5000`

## Usage

1. **Start the App**: Run `python web_app.py` and open `http://localhost:5000` in your browser

2. **Download Content**:
   - Paste a YouTube URL in the input field
   - Select format: MP4 (video) or MP3 (audio)
   - Choose quality/resolution (default is 720p for video)
   - Click "Download Now"

3. **View Downloads**:
   - Recent downloads are listed at the bottom of the page
   - Click "Download" to re-download or "Copy Link" to copy the file URL
   - Files are saved in the `downloads/` directory

4. **Browser Save Option**: Check "Save to browser" to prompt your browser to save the file directly

## Requirements

- **Python 3.6+**
- **Flask 2.0+**: Web framework
- **yt-dlp**: YouTube downloader tool (must be installed separately)
- **Tailwind CSS**: Included via CDN for styling

## Project Structure

```
youtube-downloader-web-app/
├── web_app.py              # Main Flask application
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Web interface template
├── downloads/              # Downloaded files directory
│   ├── youtube_videos/     # MP4 video files
│   └── youtube_audio/      # MP3 audio files
└── README.md               # This file
```

## How It Works

The application uses `yt-dlp`, a powerful command-line tool for downloading videos from YouTube and other sites. It provides:

- Automatic format selection based on your chosen resolution
- Audio/video merging for MP4 downloads
- Fallback mechanisms for handling YouTube's changing APIs
- Progress tracking and error handling

## Troubleshooting

- **Download fails**: Try updating yt-dlp with `pip install -U yt-dlp`
- **Port already in use**: Change the port in `web_app.py` (default is 5000)
- **Permission errors**: Ensure write permissions for the `downloads/` directory

## License

This project is open-source and available under the MIT License.

## Disclaimer

This tool is for personal use only. Please respect YouTube's terms of service and copyright laws. The developers are not responsible for misuse of this application.
# Youtube-Downloader
