from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .handlers import resolvers, controllers
from .config import *


__plugin_meta__ = PluginMetadata(
    name="链接分享解析器",
    description="NoneBot2链接分享解析器插件。解析视频、图片链接/小程序插件，tiktok、bilibili、twitter等实时发送！",
    usage="分享链接即可体验到效果",
    type="application",
    homepage="https://github.com/zhiyu1998/nonebot-plugin-resolver",
    config=Config,
    supported_adapters={ "~onebot.v11" }
)

driver = get_driver()

@driver.on_startup()
async def _():
    if rconfig.bili_ck:
        bili_credential = Credential.from_cookies(cookies_str_to_dict(rconfig.bili_ck))
        logger.info(f"bilibili credential format sucess: {bili_credential}")
        # save_cookies_to_netscape(rconfig.bili_ck, bili_cookies_file, 'bilibili.com')
    if rconfig.ytb_ck:
        save_cookies_to_netscape(rconfig.ytb_ck, ytb_cookies_file, 'youtube.com')
    # 处理黑名单 resovler
    for resolver in rconfig.black_resolvers:
        matcher = resolvers[resolver]
        if matcher:
            resolvers[resolver].destroy()
            logger.info(f"matcher {resolver} was destroyed")
    for m in controllers:
        pass


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

    # 验证保存的 cookies
    logger.info(f"cookies saved to {file_path}")

def cookies_str_to_dict(cookies_str: str) -> dict[str, str]:
    res = {}
    for cookie in cookies_str.split(';'):
        name, value = cookie.strip().split('=', 1)
        res[name] = value
    return res