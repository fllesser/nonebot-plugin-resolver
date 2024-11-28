from nonebot import logger
from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .handlers import resolvers, controllers
from .config import Config, rconfig, format_cookies


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
    format_cookies()
    # 处理黑名单 resovler
    for resolver in rconfig.black_resolvers:
        if matcher := resolvers[resolver]:
            resolvers[resolver].destroy()
            logger.info(f"解析器 {resolver} 已销毁")

