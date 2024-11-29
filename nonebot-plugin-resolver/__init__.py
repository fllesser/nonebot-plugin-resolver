from nonebot import get_driver, logger
from nonebot.plugin import PluginMetadata
from bilibili_api import Credential

from .handlers import resolvers, controllers
from .config import *
from .cookie import *

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

@driver.on_startup
async def _():
    if RCONFIG.r_bili_ck:
        pass
        # cookie_dict = cookies_str_to_dict(RCONFIG.r_bili_ck)
        # if cookie_dict["SESSDATA"]:
        #     logger.info(f"bilibili credential format sucess from cookie")
        # else:
        #     logger.error(f"配置的 bili_ck 未包含 SESSDATA 项，可能无效")
        # save_cookies_to_netscape(RCONFIG.bili_ck, bili_cookies_file, 'bilibili.com')
    if RCONFIG.r_ytb_ck:
        save_cookies_to_netscape(RCONFIG.r_ytb_ck, YTB_COOKIES_FILE, 'youtube.com')
    # 处理黑名单 resovler
    for resolver in RCONFIG.r_black_resolvers:
        if matcher := resolvers[resolver]:
            matcher.destroy()
            logger.info(f"解析器 {resolver} 已销毁")

