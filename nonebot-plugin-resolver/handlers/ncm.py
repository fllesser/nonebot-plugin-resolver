import re
import httpx

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment

from .filter import resolve_filter
from .utils import *
from ..constants import COMMON_HEADER, NETEASE_API_CN, NETEASE_TEMP_API
from ..core.common import download_audio
from ..config import *

ncm = on_regex(
    r"(music.163.com|163cn.tv)"
)

@ncm.handle()
@resolve_filter
async def ncm_handler(bot: Bot, event: Event):
    message = str(event.message)
    # 识别短链接
    if "163cn.tv" in message:
        message = re.search(r"(http:|https:)\/\/163cn\.tv\/([a-zA-Z0-9]+)", message).group(0)
        message = str(httpx.head(message, follow_redirects=True).url)

    ncm_id = re.search(r"id=(\d+)", message).group(1)
    if ncm_id is None:
        await ncm.finish(Message(f"❌ {NICKNAME}识别 | 网易云 - 获取链接失败"))
    # 拼接获取信息的链接
    ncm_detail_url = f'{NETEASE_API_CN}/song/detail?ids={ncm_id}'
    ncm_detail_resp = httpx.get(ncm_detail_url, headers=COMMON_HEADER)
    # 获取歌曲名
    ncm_song = ncm_detail_resp.json()['songs'][0]
    ncm_title = f'{ncm_song["name"]}-{ncm_song["ar"][0]["name"]}'.replace(r'[\/\?<>\\:\*\|".… ]', "")

    # 对接临时接口
    ncm_vip_data = httpx.get(f"{NETEASE_TEMP_API.replace('{}', ncm_title)}", headers=COMMON_HEADER).json()
    ncm_url = ncm_vip_data['mp3']
    ncm_cover = ncm_vip_data['img']
    await ncm.send(Message(
        [MessageSegment.image(ncm_cover), MessageSegment.text(f'{NICKNAME}识别 | 网易云音乐 - {ncm_title}')]))
    # 下载音频文件后会返回一个下载路径
    ncm_music_path = await download_audio(ncm_url)
    # 发送语音
    await ncm.send(Message(MessageSegment.record(ncm_music_path)))
    # 发送群文件
    await upload_both(bot, event, ncm_music_path, f'{ncm_title}.{ncm_music_path.split(".")[-1]}')
    if os.path.exists(ncm_music_path):
        os.unlink(ncm_music_path)