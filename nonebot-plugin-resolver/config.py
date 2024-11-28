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

def format_cookies():
    if rconfig.bili_ck:
        cookie_dict = cookies_str_to_dict(rconfig.bili_ck)
        global bili_credential
        bili_credential = Credential.from_cookies(cookie_dict)
        if cookie_dict["SESSDATA"]:
            logger.info(f"bilibili credential format sucess from cookie")
        else:
            logger.error(f"配置的 bili_ck 未包含 SESSDATA 项，可能无效")
        # save_cookies_to_netscape(rconfig.bili_ck, bili_cookies_file, 'bilibili.com')
    if rconfig.ytb_ck:
        save_cookies_to_netscape(rconfig.ytb_ck, ytb_cookies_file, 'youtube.com')

def save_cookies_to_netscape(cookies_str, file_path, domain):
    # 先检测目录是否存在
    dirpath = os.path.dirname(file_path) 
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    # 创建 MozillaCookieJar 对象
    cj = http.cookiejar.MozillaCookieJar(file_path)

    # 从字符串创建 cookies 并添加到 MozillaCookieJar 对象
    for cookie in cookies_str.split(';'):
        name, value = cookie.strip().split('=', 1)
        cj.set_cookie(http.cookiejar.Cookie(
            version=0, name=name, value=value, port=None, port_specified=False,
            domain="." + domain, domain_specified=True, domain_initial_dot=False,
            path="/", path_specified=True, secure=True,
            expires=0, discard=True, comment=None, comment_url=None,
            rest={'HttpOnly': None}, rfc2109=False,
        ))

    # 保存 cookies 到文件
    cj.save(ignore_discard=True, ignore_expires=True)
    logger.info(f"{file_path} saved sucessfully")
    
def cookies_str_to_dict(cookies_str: str) -> dict[str, str]:
    res = {}
    for cookie in cookies_str.split(';'):
        name, value = cookie.strip().split('=', 1)
        res[name] = value
    return res