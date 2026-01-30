# YT-DLP Bot - TVer Audio Track Fix

## Overview
This is a Telegram bot that uses yt-dlp to download videos from various platforms including YouTube, Twitter, TikTok, Reddit, and TVer (Japanese streaming service).

## Bug Fix
**Issue**: When downloading videos from TVer, the audio track was not being processed properly.

**Root Cause**: The `download_video` function had a default `format_id` parameter set to `"mp4"`. This format specification doesn't ensure that both video and audio streams are properly downloaded and merged, especially for streaming services like TVer that serve video and audio as separate streams.

**Solution**: Changed the default `format_id` from `"mp4"` to `"bestvideo+bestaudio/best"`. This format string tells yt-dlp to:
- Download the best quality video stream
- Download the best quality audio stream
- Merge them together into a single file
- If merging fails or separate streams aren't available, fall back to downloading the best available single-file format

## Configuration
1. Copy `ytdlp_config.py` and update the following values:
   - `api_id`: Your Telegram API ID
   - `api_hash`: Your Telegram API Hash
   - `bot_token`: Your Telegram Bot Token
   - `output_folder`: Directory for temporary downloads (default: ./downloads)
   - `max_filesize`: Maximum file size in bytes (default: 2GB)

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure FFmpeg is installed on your system (required for merging audio/video streams)

## Usage
Run the bot:
```bash
python ytdlp_bot.py
```

### Commands
- `/start` or `/help` - Show help message
- `/download <url>` - Download video from URL
- `/audio <url>` - Extract audio only from URL
- Send any URL directly - Download video from URL

### Supported Platforms
The bot works with any platform supported by yt-dlp, including:
- YouTube
- Twitter
- TikTok
- Reddit
- TVer (now with proper audio track support!)
- And many more...

## Technical Details

### Format String Explanation
- `bestvideo+bestaudio` - Downloads the best video and best audio streams separately, then merges them
- `/best` - Fallback option: if separate streams aren't available or merging fails, download the best single-file format

### Why This Fix Works for TVer
TVer, like many modern streaming services, uses DASH (Dynamic Adaptive Streaming over HTTP) or HLS (HTTP Live Streaming) protocols. These protocols serve video and audio as separate streams for adaptive bitrate streaming. The old format specification `"mp4"` would only select a video stream without ensuring audio was included. The new format `"bestvideo+bestaudio/best"` explicitly requests both streams and merges them using FFmpeg.

## Notes
- The bot requires FFmpeg to be installed for merging video and audio streams
- Downloaded files are automatically deleted after uploading to Telegram
- Progress updates are shown every 5 seconds during download and every 5% during upload
