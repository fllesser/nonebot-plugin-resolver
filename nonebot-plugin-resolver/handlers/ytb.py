import re

from nonebot import on_regex, matcher
from nonebot.adapters.onebot.v11 import MessageEvent

from .utils import auto_video_send
from ..core.ytdlp import get_video_title, ytdlp_download_video
from .filter import resolve_handler


from ..config import *

ytb = on_regex(
    r"(youtube.com|youtu.be)", priority=1
)
@ytb.handle()
@resolve_handler
async def ytb_handler(event: MessageEvent):
    url = re.search(
        r"(?:https?:\/\/)?(www\.)?youtube\.com\/[A-Za-z\d._?%&+\-=\/#]*|(?:https?:\/\/)?youtu\.be\/[A-Za-z\d._?%&+\-=\/#]*",
        str(event.message).strip())[0]

    title = await get_video_title(url, ytb_cookies_file, PROXY)
    if not title:
        title = "网络繁忙，获取标题失败"
    await ytb.send(f"{GLOBAL_NICKNAME}识别：油管 - {title}\n正在下载视频...")

    video_path = await ytdlp_download_video(
        url = url, path = (rpath / 'temp').absolute(), type="ytb",cookiefile = ytb_cookies_file, proxy = PROXY)
    if video_path:
        await auto_video_send(event, video_path)
    else:
        await ytb.finish("网络繁忙，下载视频出错")


