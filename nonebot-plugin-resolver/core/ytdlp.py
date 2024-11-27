import yt_dlp
import random
import asyncio

from nonebot import logger
from pathlib import Path

async def get_video_title(url: str, cookiefile: str = '', proxy: str = '') -> str:
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'force_generic_extractor': True,
    }
    if proxy:
        ydl_opts['proxy'] = proxy
    if cookiefile:
        ydl_opts['cookiefile'] = f"data/nonebot-plugin-resolver/cookie/{cookiefile}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
            return info_dict.get('title', '')
    except Exception as e:
        logger.error(e)
        return ''
        
async def ytdlp_download_video(url: str, path: str, type: str, height: int = 1080, cookiefile: str = '', proxy: str = '') -> str:
    filename = f"{path}/{type}-{random.randint(1, 10000)}"
    ydl_opts = {
        'outtmpl': f'{filename}.%(ext)s',
        'merge_output_format': 'mp4',
        'format': f'best[height<={height}]',
    }

    if proxy:
        ydl_opts['proxy'] = proxy
    if cookiefile:
        ydl_opts['cookiefile'] = f"data/nonebot-plugin-resolver/cookie/{cookiefile}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        return f'{filename}.mp4'
      
    except Exception as e:
        logger.error(e)
        return ''


  