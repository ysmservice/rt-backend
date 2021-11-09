# RT.Blueprints - OAuth Test

from backend import TypedSanic, TypedBlueprint, hCaptcha, Request
from backend.utils import cooldown
from sanic.response import text

from time import time


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

    captcha = hCaptcha(
        app, app.ctx.secret["hCaptcha"]["test"], app.ctx.secret["secret_key"],
        "captcha.html", "sitekey", "20000000-ffff-ffff-ffff-000000000002"
            if app.ctx.test else "0a50268d-fa1e-405f-9029-710309aad1b0"
    )

    @bp.route("/captcha/start")
    async def captcha_start(_):
        return await captcha.start(
            "userdata", {"data": "VeryImportantData", "time": time()},
            redirect_url="/test/captcha/end"
        )

    @bp.route("/captcha/end/<data>", methods=["GET", "POST"])
    @cooldown(bp, 10)
    @captcha.end(check=lambda data: time() - data["time"] <= 15)
    async def captcha_end(request: Request, data: dict):
        return text(f"CaptchaResult:{request.ctx.success} Data:{data}")
