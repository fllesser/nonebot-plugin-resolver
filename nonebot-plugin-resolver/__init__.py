from nonebot.plugin import PluginMetadata

from .handlers import resolvers
from .config import Config, rconfig


__plugin_meta__ = PluginMetadata(
    name="链接分享解析器",
    description="NoneBot2链接分享解析器插件。解析视频、图片链接/小程序插件，tiktok、bilibili、twitter等实时发送！",
    usage="分享链接即可体验到效果",
    type="application",
    homepage="https://github.com/zhiyu1998/nonebot-plugin-resolver",
    config=Config,
    supported_adapters={ "~onebot.v11" }
)

# 处理黑名单
if rconfig.black_resolvers:
    for resolver in rconfig.black_resolvers:
        resolvers[resolver].destroy()