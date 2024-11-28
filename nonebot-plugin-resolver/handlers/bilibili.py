import re
import httpx

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment

from bilibili_api import video, live, article
from bilibili_api.favorite_list import get_video_favorite_list_content
from bilibili_api.opus import Opus
from urllib.parse import parse_qs, urlparse
from json.decoder import JSONDecodeError

from .utils import *

from ..constants import BILIBILI_HEADER
from ..core.bili23 import extra_bili_info, av_to_bv
from ..core.ytdlp import ytdlp_download_video
from ..core.common import delete_boring_characters

from ..config import *

from .filter import resolve_handler

bilibili = on_regex(
    r"(bilibili.com|b23.tv|^BV[0-9a-zA-Z]{10}$)", priority=1
)

@bilibili.handle()
@resolve_handler
async def bilibili_handler(bot: Bot, event: Event) -> None:

    """
        哔哩哔哩解析
    :param bot:
    :param event:
    :return:
    """
    # 所有消息
    segs = []
    will_delete_id = 0

    # 消息
    url: str = str(event.message).strip()
    # 正则匹配
    url_reg = r"(http:|https:)\/\/(space|www|live).bilibili.com\/[A-Za-z\d._?%&+\-=\/#]*"
    b_short_rex = r"(http:|https:)\/\/b23.tv\/[A-Za-z\d._?%&+\-=\/#]*"
    # BV处理
    if re.match(r'^BV[1-9a-zA-Z]{10}$', url):
        url = 'https://www.bilibili.com/video/' + url
    # 处理短号、小程序问题
    if 'b23.tv' in url or ('b23.tv' and 'QQ小程序' in url):
        b_short_url = re.search(b_short_rex, url.replace("\\", ""))[0]
        resp = httpx.get(b_short_url, headers=BILIBILI_HEADER, follow_redirects=True)
        url: str = str(resp.url)
    else:
        url: str = re.search(url_reg, url).group(0)
    # ===============发现解析的是动态，转移一下===============
    if ('t.bilibili.com' in url or '/opus' in url) and bili_credential:
        # 去除多余的参数
        if '?' in url:
            url = url[:url.index('?')]
        dynamic_id = int(re.search(r'[^/]+(?!.*/)', url)[0])
        dynamic_info = await Opus(dynamic_id, bili_credential).get_info()
        # 这里比较复杂，暂时不用管，使用下面这个算法即可实现哔哩哔哩动态转发
        if dynamic_info is not None:
            title = dynamic_info['item']['basic']['title']
            paragraphs = []
            for module in dynamic_info['item']['modules']:
                if 'module_content' in module:
                    paragraphs = module['module_content']['paragraphs']
                    break
            desc = paragraphs[0]['text']['nodes'][0]['word']['words']
            pics = paragraphs[1]['pic']['pics']
            await bilibili.send(Message(f"{GLOBAL_NICKNAME}识别：B站动态，{title}\n{desc}"))
            send_pics = []
            for pic in pics:
                img = pic['url']
                send_pics.append(make_node_segment(bot.self_id, MessageSegment.image(img)))
            # 发送异步后的数据
            await send_forward_both(bot, event, send_pics)
        return
    # 直播间识别
    if 'live' in url:
        # https://live.bilibili.com/30528999?hotRank=0
        room_id = re.search(r'\/(\d+)$', url).group(1)
        room = live.LiveRoom(room_display_id=int(room_id))
        room_info = (await room.get_room_info())['room_info']
        title, cover, keyframe = room_info['title'], room_info['cover'], room_info['keyframe']
        await bilibili.send(Message([MessageSegment.image(cover), MessageSegment.image(keyframe),
                                   MessageSegment.text(f"{GLOBAL_NICKNAME}识别：哔哩哔哩直播，{title}")]))
        return
    # 专栏识别
    if 'read' in url:
        read_id = re.search(r'read\/cv(\d+)', url).group(1)
        ar = article.Article(read_id)
        # 如果专栏为公开笔记，则转换为笔记类
        # NOTE: 笔记类的函数与专栏类的函数基本一致
        if ar.is_note():
            ar = ar.turn_to_note()
        # 加载内容
        await ar.fetch_content()
        markdown_path = rpath / 'article.md'
        with open(markdown_path, 'w', encoding='utf8') as f:
            f.write(ar.markdown())
        await bilibili.send(Message(f"{GLOBAL_NICKNAME}识别：哔哩哔哩专栏"))
        await bilibili.finish(Message(MessageSegment(type="file", data={ "file": markdown_path })))
    # 收藏夹识别
    if 'favlist' in url and bili_credential:
        # https://space.bilibili.com/22990202/favlist?fid=2344812202
        fav_id = re.search(r'favlist\?fid=(\d+)', url).group(1)
        fav_list = (await get_video_favorite_list_content(fav_id))['medias'][:10]
        favs = []
        for fav in fav_list:
            title, cover, intro, link = fav['title'], fav['cover'], fav['intro'], fav['link']
            logger.info(title, cover, intro)
            favs.append(
                [MessageSegment.image(cover),
                 MessageSegment.text(f'🧉 标题：{title}\n📝 简介：{intro}\n🔗 链接：{link}')])
        await bilibili.send(f'{GLOBAL_NICKNAME}识别：哔哩哔哩收藏夹，正在为你找出相关链接请稍等...')
        await bilibili.finish(make_node_segment(bot.self_id, favs))
    # 获取视频信息
    will_delete_id: int = (await bilibili.send(f'{GLOBAL_NICKNAME}识别：哔哩哔哩, 解析中.....'))["message_id"]
    video_id = re.search(r"video\/[^\?\/ ]+", url)[0].split('/')[1]
    if "av" in video_id:
        v = video.Video(aid=int(video_id.split("av")[1]), credential=bili_credential)
    else:
        v = video.Video(bvid=video_id, credential=bili_credential)
    try:
        video_info = await v.get_info()
    except Exception as e:
        await bilibili.finish(Message(f"{GLOBAL_NICKNAME}识别：哔哩哔哩，出错，{e}"))
    if video_info is None:
        await bilibili.finish(Message(f"{GLOBAL_NICKNAME}识别：哔哩哔哩，出错，无法获取数据！"))
    video_title, video_cover, video_desc, video_duration = video_info['title'], video_info['pic'], video_info['desc'], \
        video_info['duration']
    # 校准 分 p 的情况
    page_num = 0
    if 'pages' in video_info:
        # 解析URL
        parsed_url = urlparse(url)
        # 检查是否有查询字符串
        if parsed_url.query:
            # 解析查询字符串中的参数
            query_params = parse_qs(parsed_url.query)
            # 获取指定参数的值，如果参数不存在，则返回None
            page_num = int(query_params.get('p', [1])[0]) - 1
        else:
            page_num = 0
        if 'duration' in video_info['pages'][page_num]:
            video_duration = video_info['pages'][page_num].get('duration', video_info.get('duration'))
        else:
            # 如果索引超出范围，使用 video_info['duration'] 或者其他默认值
            video_duration = video_info.get('duration', 0)
    # 删除特殊字符
    video_title = delete_boring_characters(video_title)
    # 截断下载时间比较长的视频
    online = await v.get_online()
    online_str = f'🏄‍♂️ 总共 {online["total"]} 人在观看，{online["count"]} 人在网页端观看'
    segs.append(MessageSegment.image(video_cover))
    segs.append(Message(f"{video_title}\n{extra_bili_info(video_info)}\n📝 简介：{video_desc}\n{online_str}"))
    if video_duration > VIDEO_DURATION_MAXIMUM:
        segs.append(Message(f"⚠️ 当前视频时长 {video_duration // 60} 分钟，超过管理员设置的最长时间 {VIDEO_DURATION_MAXIMUM // 60} 分钟!"))
    else:
        # 下载视频和音频
        try:
            video_path = await ytdlp_download_video(
                url = url, path = (rpath / 'temp').absolute(), type = 'bilibili', cookiefile=bili_cookies_file)
            if video_path.endswith('mp4'):
                segs.append(await get_video_seg(video_path))
            else:
                segs.append(Message(f"视频下载失败，错误：{video_path}"))
        except Exception as e:
            logger.error(f"下载视频失败，错误为\n{e}")
            segs.append(Message(f"下载视频失败，错误为\n{e}"))
     # 这里是总结内容，如果写了 cookie 就可以
    if bili_credential:
        ai_conclusion = await v.get_ai_conclusion(await v.get_cid(0))
        if ai_conclusion['model_result']['summary'] != '':
            segs.append(Message("bilibili AI总结:\n" + ai_conclusion['model_result']['summary']))
    await send_forward_both(bot, event, make_node_segment(bot.self_id, segs))
    await bot.delete_msg(message_id = will_delete_id)

