# RT.Blueprints - OAuth

from sanic.response import redirect

from backend import TypedSanic, TypedBlueprint, Request
from backend.utils import api, cooldown, CoolDown


bp = TypedBlueprint("DiscordLogin", "/account")


def on_load(app: TypedSanic):
    @bp.route("/")
    @cooldown(bp, 0.4)
    @app.ctx.oauth.require_login(force=True)
    async def account(request: Request):
        data = {"login": bool(request.ctx.user)}
        if data["login"]:
            data["user_name"] = str(request.ctx.user)
        return api("ok", data)

    @bp.route("/login")
    @CoolDown(4, 10, "クールダウン中です。{}秒後にもう一度お試しください。")
    @app.ctx.oauth.require_login()
    async def login(request: Request):
        return redirect("/")

    @bp.route("/logout")
    @cooldown(bp, 5)
    @app.ctx.oauth.require_login(force=True)
    async def logout(request: Request):
        response = redirect("/")
        if request.ctx.user:
            del response.cookies["session"]
        return response