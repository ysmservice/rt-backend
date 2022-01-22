# RT.Blueprints.API - Dashboard

from __future__ import annotations

from sanic.response import json
from sanic import Blueprint

from backend.rt_module.src.setting import CommandData
from backend.utils import api, CoolDown, try_loads
from backend import TypedSanic, Request, logger


data: dict[str, CommandData] = {}
def log(mode, msg, extend=""):
    return getattr(logger, mode)(f"[Dashboard{extend}] {msg}")


def on_load(app: TypedSanic):
    async def update_dashboard_data(new_data: dict[CommandData]):
        global data
        data = new_data
        log("info", "Update", ".data")
    app.ctx.rtc.set_event(update_dashboard_data, "dashboard.update")


    @app.get("/api/dashboard/get")
    async def get(_: Request):
        if data:
            return api("Ok", {
                "data": data, "guilds": {
                    guild["name"]: guild["id"]
                    for guild in await app.ctx.rtc.request("get_")
                }
            })
        else:
            return api("Error", None, 503)


    @app.post("/api/dashboard/post")
    @app.ctx.oauth.require_login(True)
    @CoolDown(1, 1.3, "リクエストしすぎです。| Too many requests.")
    async def run(request: Request):
        if request.ctx.user:
            return api(
                "Ok", await app.ctx.rtc.request("dashboard.run", try_loads(request))
            )
        else:
            return api("Error", "Require login", 403)