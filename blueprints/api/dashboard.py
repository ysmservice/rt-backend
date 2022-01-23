# RT.Blueprints.API - Dashboard

from __future__ import annotations

from functools import wraps

from backend.rt_module.src.setting import CommandData
from backend.utils import api, CoolDown, try_loads
from backend import TypedSanic, Request, logger


data: dict[str, CommandData] = {}
def log(mode, msg, extend=""):
    return getattr(logger, mode)(f"[Dashboard{extend}] {msg}")
MANYERR = "リクエストしすぎです。| Too many requests."


def on_load(app: TypedSanic):
    async def update_dashboard_data(new_data: dict[CommandData]):
        global data
        data = new_data
        log("info", "Update", ".data")
    app.ctx.rtc.set_event(update_dashboard_data, "dashboard.update")


    def check_user(func):
        # 普通のAPIにつけるデコレータ, エイリアス
        @wraps(func)
        async def new(request, *args, **kwargs):
            if request.ctx.user:
                return await func(request, *args, **kwargs)
            else:
                return api("Error", None, 403)
        return new


    @app.get("/api/dashboard/get/channels/<guild_id:int>")
    @app.ctx.oauth.require_login(True)
    @CoolDown(3, 1, MANYERR)
    @check_user
    async def get_channels(_: Request, guild_id: int):
        "チャンネルのリストを取得します。"
        if guild := await app.ctx.rtc.request("get_guild", guild_id):
            return api("Ok", {
                channel["id"]: channel["name"]
                for channel in guild["channels"]
            })
        return api("Error", "Not Found", 404)


    @app.get("/api/dashboard/get/commands")
    @app.ctx.oauth.require_login(True)
    @CoolDown(3, 1, MANYERR)
    @check_user
    async def get_comands(request: Request):
        "ダッシュボードに表示するコマンドのデータを返す。"
        if data:
            return api("Ok", {
                "data": data, "guilds": {
                    guild["id"]: guild["name"]
                    for guild in await app.ctx.rtc.request(
                        "get_guilds", request.ctx.user.id
                    )
                }
            })
        else:
            return api("Error", None, 503)


    @app.post("/api/dashboard/post")
    @check_user
    async def run_command(request: Request):
        "コマンドを実行する。"
        return api(
            "Ok", await app.ctx.rtc.request("dashboard.run", try_loads(request))
        )