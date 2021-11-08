# RT.Blueprints - OAuth

from sanic.response import redirect

from backend import TypedSanic, TypedBlueprint, Request
from backend.utils import cooldown


bp = TypedBlueprint("DiscordLogin", "/discord")


def on_load(app: TypedSanic):
    @bp.route("/login")
    @cooldown(bp, 10, "クールダウン中です。{}秒後にもう一度お試しください。")
    @app.ctx.oauth.require_login()
    async def login(request: Request):
        return redirect("/")

    @bp.route("/logout")
    @cooldown(bp, 3)
    @app.ctx.oauth.require_login(force=True)
    async def logout(request: Request):
        response = redirect("/")
        if request.ctx.user:
            del response.cookies["session"]
        return response