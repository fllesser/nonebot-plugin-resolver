import os
import http.cookiejar

from nonebot import logger

from pydantic import BaseModel
from nonebot import get_plugin_config
from pathlib import Path
from bilibili_api import Credential

class Config(BaseModel):
    xhs_ck: str = ''
    douyin_ck: str = ''
    bili_ck: str = ''
    ytb_ck: str = ''
    is_oversea: bool = False
    r_global_nickname: str = ''
    resolver_proxy: str = 'http://127.0.0.1:7890'
    max_video_height: int = 1080
    video_duration_maximum: int = 480
    black_resolvers: list[str] = []

# 插件数据目录
rpath: Path = Path() / 'data' /'nonebot-plugin-resolver'
# 配置加载
rconfig: Config = get_plugin_config(Config)
# 全局名称
GLOBAL_NICKNAME: str = rconfig.r_global_nickname
# 根据是否为国外机器声明代理
PROXY: str = "" if not rconfig.is_oversea else rconfig.resolver_proxy
# 哔哩哔哩限制的最大视频时长（默认8分钟）单位：秒
VIDEO_DURATION_MAXIMUM: int = rconfig.video_duration_maximum
# yt-dlp 下载视频最大高度
HEIGHT: int = rconfig.max_video_height

# format config
ytb_cookies_file = (rpath / 'cookie' / 'ytb_cookies.txt').absolute()
bili_cookies_file = (rpath / 'cookie' / 'bili_cookies.txt').absolute()
bili_credential: Credential = None

