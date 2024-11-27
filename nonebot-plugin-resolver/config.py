from pydantic import BaseModel
from typing import Optional


class Config(BaseModel):
    xhs_ck: Optional[str] = ''
    douyin_ck: Optional[str] = ''
    bili_ck: Optional[str] = ''
    ytb_ck: Optional[str] = ''
    is_oversea: Optional[bool] = False
    r_global_nickname: Optional[str] = ''
    resolver_proxy: Optional[str] = 'http://127.0.0.1:7890'
    max_video_height: Optional[int] = 1080
    video_duration_maximum: Optional[int] = 480
    global_resolve_controller: Optional[str] = ""
