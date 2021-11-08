# RT.Blueprints - OAuth Test

from sanic.response import text

from backend import TypedSanic, TypedBlueprint


bp = TypedBlueprint("Test", "/test")


def on_load(app: TypedSanic):
    @bp.route("/oauth/noforce")
    @app.ctx.oauth.require_login()
    async def oauth(request: app.ctx.oauth.TypedRequest):
        return text(f"UserName: {request.ctx.user.name}, ID: {request.ctx.user.id}")

    @bp.route("/oauth/force")
    @app.ctx.oauth.require_login(True)
    async def oauth_force(request: app.ctx.oauth.TypedRequest):
        if request.ctx.user:
            return text(
                f"UserName: {request.ctx.user.name}, ID: {request.ctx.user.id}"
            )
        else:
            return text("None User")