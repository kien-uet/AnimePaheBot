import asyncio
import sys

# Fix event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
from pyrogram.types import Message
import ytdlp_config as config
import yt_dlp
import os
import re
from urllib.parse import urlparse
import time
from traceback import print_exc

app = Client(
    'yt-dlp-bot',
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
    workers=32,
    max_concurrent_transmissions=8,
    sleep_threshold=30
)

def youtube_url_validation(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url)

@app.on_message(filters.command(['start', 'help']))
async def start(client, message: Message):
    await message.reply(
        "**Send me a video link** and I'll download it for you, works with **YouTube**, **Twitter**, **TikTok**, **Reddit** and more.\n\n"
        "_Powered by_ [yt-dlp](https://github.com/yt-dlp/yt-dlp/)",
        disable_web_page_preview=True
    )

async def download_video(client, message: Message, url: str, audio=False, format_id="bestvideo+bestaudio/best"):
    url_info = urlparse(url)
    if not url_info.scheme:
        await message.reply('Invalid URL')
        return
    
    if url_info.netloc in ['www.youtube.com', 'youtu.be', 'youtube.com']:
        if not youtube_url_validation(url):
            await message.reply('Invalid YouTube URL')
            return

    video_title = f"{message.from_user.id}_{int(time.time() * 1000)}"
    status_msg = await message.reply('Downloading...')
    last_update = {'time': time.time()}
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                current_time = time.time()
                if current_time - last_update['time'] >= 5:
                    perc = round(d.get('downloaded_bytes', 0) * 100 / d.get('total_bytes', 1))
                    asyncio.create_task(
                        status_msg.edit(f"Downloading {d['info_dict'].get('title', 'video')}\n\n{perc}%")
                    )
                    last_update['time'] = current_time
            except:
                pass

    ydl_opts = {
        'format': format_id,
        'outtmpl': f'{config.output_folder}/{video_title}.%(ext)s',
        'progress_hooks': [progress_hook],
        'max_filesize': config.max_filesize,
        'writesubtitles': True,
        'subtitleslangs': ['all'],
        'embedsubtitles': True,
        'postprocessors': []
    }

    if audio:
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        })
    else:
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegEmbedSubtitle',
        })

    if hasattr(config, 'proxy') and config.proxy:
        ydl_opts['proxy'] = config.proxy

    if hasattr(config, 'downloader') and config.downloader:
        ydl_opts['external_downloader'] = config.downloader

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = info['requested_downloads'][0]['filepath']
            
        await status_msg.edit('Sending file to Telegram...')

        last_upload_update = {'perc': 0}
        async def upload_progress(current, total):
            perc = round(current * 100 / total)
            if perc >= last_upload_update['perc'] + 5:
                try:
                    await status_msg.edit(f'Uploading to Telegram... {perc}%')
                    last_upload_update['perc'] = perc
                except:
                    pass

        if audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=filepath,
                reply_to_message_id=message.id,
                progress=upload_progress
            )
        else:
            width = info['requested_downloads'][0].get('width', 0)
            height = info['requested_downloads'][0].get('height', 0)
            duration = info.get('duration', 0)
            
            thumb_path = None
            try:
                thumb_path = f'{config.output_folder}/{video_title}.jpg'
                proc = await asyncio.create_subprocess_shell(
                    f'ffmpeg -i "{filepath}" -ss 00:00:01.000 -vframes 1 "{thumb_path}"',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
            except:
                thumb_path = None

            await client.send_video(
                chat_id=message.chat.id,
                video=filepath,
                width=width,
                height=height,
                duration=int(duration) if duration else 0,
                thumb=thumb_path,
                reply_to_message_id=message.id,
                progress=upload_progress
            )
            
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)

        await status_msg.delete()
        
    except yt_dlp.utils.DownloadError:
        await status_msg.edit('Invalid URL or download failed')
    except Exception as e:
        print_exc()
        await status_msg.edit(f'Error: {str(e)[:100]}')
    finally:
        for file in os.listdir(config.output_folder):
            if file.startswith(str(video_title)):
                try:
                    os.remove(f'{config.output_folder}/{file}')
                except:
                    pass

@app.on_message(filters.command('download'))
async def download_command(client, message: Message):
    try:
        url = message.text.split(' ', 1)[1]
    except:
        await message.reply('Invalid usage, use `/download url`')
        return
    await download_video(client, message, url)

@app.on_message(filters.command('audio'))
async def audio_command(client, message: Message):
    try:
        url = message.text.split(' ', 1)[1]
    except:
        await message.reply('Invalid usage, use `/audio url`')
        return
    await download_video(client, message, url, audio=True)

@app.on_message(filters.private & filters.text & ~filters.command(['start', 'help', 'download', 'audio']))
async def handle_private_messages(client, message: Message):
    url = message.text
    if re.search(r'https?://\S+', url):
        await download_video(client, message, url)
    else:
        await message.reply('Please send a valid URL')

print("Bot started!")
app.run()
