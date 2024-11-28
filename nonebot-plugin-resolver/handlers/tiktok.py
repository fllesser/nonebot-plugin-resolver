import re, httpx

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Event, Message

from .filter import resolve_handler
from .utils import auto_video_send
from ..core.ytdlp import get_video_title, ytdlp_download_video

from ..config import *

tiktok = on_regex(
    r"(www.tiktok.com|vt.tiktok.com|vm.tiktok.com)", priority=1
)

@tiktok.handle()
@resolve_handler
async def tiktok_handler(event: Event) -> None:
    """
        tiktok解析
    :param event:
    :return:
    """
    # 消息
    url: str = str(event.message).strip()

    url_reg = r"(http:|https:)\/\/www.tiktok.com\/[A-Za-z\d._?%&+\-=\/#@]*"
    url_short_reg = r"(http:|https:)\/\/vt.tiktok.com\/[A-Za-z\d._?%&+\-=\/#]*"
    url_short_reg2 = r"(http:|https:)\/\/vm.tiktok.com\/[A-Za-z\d._?%&+\-=\/#]*"

    if "vt.tiktok" in url:
        temp_url = re.search(url_short_reg, url)[0]
        temp_resp = httpx.get(temp_url, follow_redirects=True, proxies=PROXY)
        url = temp_resp.url
    elif "vm.tiktok" in url:
        temp_url = re.search(url_short_reg2, url)[0]
        temp_resp = httpx.get(temp_url, headers={ "User-Agent": "facebookexternalhit/1.1" }, follow_redirects=True,
                              proxies=PROXY)
        url = str(temp_resp.url)
        # logger.info(url)
    else:
        url = re.search(url_reg, url)[0]
    title = await get_video_title(url = url, proxy = PROXY)
    if not title:
        title ="网络繁忙，获取标题失败"
    await tiktok.send(Message(f"{GLOBAL_NICKNAME}识别：TikTok - {title}"))

    video_path = await ytdlp_download_video(
        url = url, path = (rpath / 'temp').absolute(), type = 'tiktok', proxy = PROXY)
    if video_path:
        await auto_video_send(event, video_path)
    else:
        await tiktok.finish("网络繁忙，下载视频出错")


