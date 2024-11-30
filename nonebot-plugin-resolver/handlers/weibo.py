import os, re, asyncio, json, httpx

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment
from nonebot import logger

from .filter import resolve_filter
from .utils import auto_video_send, make_node_segment, send_forward_both
from ..constants.common import COMMON_HEADER
from ..constants.weibo import WEIBO_SINGLE_INFO
from ..core.common import download_img, download_video
from ..core.weibo import mid2id

from ..config import *

weibo = on_regex(
    r"(weibo.com|m.weibo.cn)"
)


@weibo.handle()
@resolve_filter
async def weibo_handler(bot: Bot, event: Event):
    message = str(event.message)
    weibo_id = None
    reg = r'(jumpUrl|qqdocurl)": ?"(.*?)"'

    # 处理卡片问题
    if 'com.tencent.structmsg' or 'com.tencent.miniapp' in message:
        match = re.search(reg, message)
        print(match)
        if match:
            get_url = match.group(2)
            print(get_url)
            if get_url:
                message = json.loads('"' + get_url + '"')
    else:
        message = message
    # logger.info(message)
    # 判断是否包含 "m.weibo.cn"
    if "m.weibo.cn" in message:
        # https://m.weibo.cn/detail/4976424138313924
        match = re.search(r'(?<=detail/)[A-Za-z\d]+', message) or re.search(r'(?<=m.weibo.cn/)[A-Za-z\d]+/[A-Za-z\d]+',
                                                                            message)
        weibo_id = match.group(0) if match else None

    # 判断是否包含 "weibo.com/tv/show" 且包含 "mid="
    elif "weibo.com/tv/show" in message and "mid=" in message:
        # https://weibo.com/tv/show/1034:5007449447661594?mid=5007452630158934
        match = re.search(r'(?<=mid=)[A-Za-z\d]+', message)
        if match:
            weibo_id = mid2id(match.group(0))
    # 判断是否包含 "weibo.com/show" 且包含 "fid="
    elif "weibo.com/show" in message and "fid=" in message:
        # https://weibo.com/show?fid=1034:5007449447661594
        match = re.search(r'(?<=fid=)[\d]+:[\d]+', message)
        # 懒得写了
    # 判断是否包含 "weibo.com"
    elif "weibo.com" in message:
        # https://weibo.com/1707895270/5006106478773472
        match = re.search(r'(?<=weibo.com/)[A-Za-z\d]+/[A-Za-z\d]+', message)
        weibo_id = match.group(0) if match else None

    # 无法获取到id则返回失败信息
    if not weibo_id:
        await weibo.finish(Message("解析失败：无法获取到微博的 id"))
    # 最终获取到的 id
    weibo_id = weibo_id.split("/")[1] if "/" in weibo_id else weibo_id
    logger.info(weibo_id)
    # 请求数据
    resp = httpx.get(WEIBO_SINGLE_INFO.replace('{}', weibo_id), headers={
                                                                            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                                                                            "cookie": "_T_WM=40835919903; WEIBOCN_FROM=1110006030; MLOGIN=0; XSRF-TOKEN=4399c8",
                                                                            "Referer": f"https://m.weibo.cn/detail/{id}",
                                                                        } | COMMON_HEADER).json()
    weibo_data = resp['data']
    logger.info(weibo_data)
    text, status_title, source, region_name, pics, page_info = (weibo_data.get(key, None) for key in
                                                                ['text', 'status_title', 'source', 'region_name',
                                                                 'pics', 'page_info'])
    # 发送消息
    await weibo.send(
        Message(
            f"{NICKNAME}识别 | 微博 - {re.sub(r'<[^>]+>', '', text)}\n{status_title}\n{source}\t{region_name if region_name else ''}"))
    if pics:
        pics = map(lambda x: x['url'], pics)
        download_img_funcs = [asyncio.create_task(download_img(item, '', headers={
                                                                                     "Referer": "http://blog.sina.com.cn/"
                                                                                 } | COMMON_HEADER)) for item in pics]
        links_path = await asyncio.gather(*download_img_funcs)
        # 发送图片
        links = make_node_segment(bot.self_id,
                                  [MessageSegment.image(f"file://{link}") for link in links_path])
        # 发送异步后的数据
        await send_forward_both(bot, event, links)
        # 清除图片
        for temp in links_path:
            os.unlink(temp)
    if page_info:
        video_url = page_info.get('urls', '').get('mp4_720p_mp4', '') or page_info.get('urls', '').get('mp4_hd_mp4', '')
        if video_url:
            path = await download_video(video_url, ext_headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "referer": "https://weibo.com/"
            })
            await auto_video_send(event, path)