# Configuration for yt-dlp bot
# This is a sample configuration file. Update with your actual values.

import os

# Telegram API credentials
api_id = int(os.environ.get("API_ID", "1234567"))
api_hash = os.environ.get("API_HASH", "")
bot_token = os.environ.get("BOT_TOKEN", "")

# Download settings
output_folder = os.environ.get("DOWNLOAD_DIR", "./downloads")
max_filesize = int(os.environ.get("MAX_FILESIZE", "2147483648"))  # 2GB default

# Optional: Proxy settings
proxy = os.environ.get("PROXY", None)

# Optional: External downloader
downloader = os.environ.get("DOWNLOADER", None)

# Ensure download folder exists
os.makedirs(output_folder, exist_ok=True)
