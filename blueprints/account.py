# RT.Blueprints.API - Account

from backend import TypedBlueprint, TypedSanic, Request
from utils import api, cooldown


bp = TypedBlueprint("API.Account")


def on_load(app: TypedSanic):
    @bp.route("/account")
    @app.ctx.oauth.require_login(force=True)
    async def account(request: Request):
        data = {"login": bool(request.ctx.user)}
        if data["login"]:
            data["user_name"] = str(request.ctx.user)
        return api("ok", data)