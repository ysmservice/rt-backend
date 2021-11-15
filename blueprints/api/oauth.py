# RT.Blueprints - OAuth

from sanic.response import redirect

from backend import TypedSanic, TypedBlueprint, Request
from backend.utils import api, cooldown, CoolDown, is_okip, try_loads


bp = TypedBlueprint("DiscordLogin", "/account")


def on_load(app: TypedSanic):
    @bp.route("/")
    @app.ctx.oauth.require_login(force=True)
    async def account(request: Request):
        data = {"login": bool(request.ctx.user)}
        if data["login"]:
            data["user_name"] = str(request.ctx.user)
            data["language"] = app.ctx.get_language(request.ctx.user.id)
            data["icon"] = getattr(
                request.ctx.user.avatar, "url",
                "/img/discord.jpg"
            )
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

    @bp.post("/language")
    @is_okip(bp)
    async def update_language(request: Request):
        app.ctx.languages = {
            int(key): value for key, value in try_loads(request).items()
        }
        return api("ok", None)

    app.ctx.languages = {}
    app.ctx.get_language = lambda user_id: app.ctx.languages.get(user_id, "ja")