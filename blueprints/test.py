# RT.Blueprints - OAuth Test

from backend import TypedSanic, TypedBlueprint, hCaptcha, Request
from backend.utils import cooldown, CoolDown
from sanic.response import text

from time import time


bp = TypedBlueprint("Test", "/test")


def on_load(app: TypedSanic):
    @bp.route("/oauth/noforce")
    @cooldown(bp, 10)
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

    if "hCaptcha" not in app.ctx.secret:
        return

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

    @bp.route("/captcha/end", methods=["GET", "POST"])
    @cooldown(bp, 10)
    @captcha.end(
        check=lambda data: time() - data["time"] <= 30
    )
    async def captcha_end(request: Request):
        return text(f"CaptchaResult:{request.ctx.success} Data:{request.ctx.data}")

    @bp.route("/cooldown")
    @CoolDown(5, 3)
    async def cooldown_test(request: Request):
        return text("There is nothing.")