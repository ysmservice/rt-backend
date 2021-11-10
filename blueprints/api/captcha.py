# RT.Blueprints.API - Captcha

from backend import (
    TypedSanic, TypedBlueprint, Request, WebSocket, PacketData, hCaptcha
)
from backend.utils import cooldown, is_okip

from asyncio import Queue
from time import time


bp = TypedBlueprint("API.Captcha")
queue = Queue()
TIMEOUT = 300
COOLDOWN = "クールダウン中です。{}秒後にもう一度お試しください。"


def on_load(app: TypedSanic):
    captcha = hCaptcha(
        app, app.ctx.secret["hCaptcha"]["test" if app.ctx.test else "production"],
        app.ctx.secret["secret_key"], "captcha.html", "sitekey",
        "20000000-ffff-ffff-ffff-000000000002" if app.ctx.test
        else "0a50268d-fa1e-405f-9029-710309aad1b0"
    )

    @app.route("/captcha")
    @cooldown(bp, 5, COOLDOWN)
    @app.ctx.oauth.require_login()
    async def captcha_first(request: Request):
        return captcha.start(
            "userdata", {
                "user_id": request.ctx.user.id, "timeout": time() + TIMEOUT
            }, redirect_url="/captcha/end"
        )

    @app.route("/captcha/end")
    @cooldown(bp, 5, COOLDOWN)
    @captcha.end(check=lambda data: data["timeout"] > time())
    async def captcha_end(request: Request):
        if request.ctx.success:
            # もし認証が成功したのならキューにユーザーIDを追加する。
            await queue.put(request.ctx.data["user_id"])
        return app.ctx.template(
            "captcha_result.html", keys={
                "result": "認証に成功しました！" if request.ctx.success \
                    else "認証に失敗しました。もう一度五秒後に挑戦してください。"
            }
        )

    @bp.websocket("/captcha")
    @is_okip(bp)
    class CaptchaWebSocket(WebSocket):
        async def on_ready(self, _):
            # ユーザーが認証を通ったのならBotに認証が成功したことを伝える。
            await self.send("on_success", str(await queue.get()))