import os
import http.cookiejar
from nonebot import logger

def save_cookies_to_netscape(cookies_str, file_path, domain):
    # 先检测目录是否存在
    dir_path = os.path.dirname(file_path) 
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    # 创建 MozillaCookieJar 对象
    cj = http.cookiejar.MozillaCookieJar(file_path)

    # 从字符串创建 cookies 并添加到 MozillaCookieJar 对象
    for cookie in cookies_str.split('; '):
        name, value = cookie.split('=', 1)
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