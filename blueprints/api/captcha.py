# RT.Blueprints.API - Captcha

from backend import TypedSanic, TypedBlueprint, Request, WebSocket, PacketData
from backend.utils import cooldown


bp = TypedBlueprint("API.Captcha")


def on_load(app: TypedSanic):
    @app.route("/captcha")
    @cooldown(bp, 10, "クールダウン中です。{}秒後にもう一度お試しください。")
    @app.ctx.oauth.require_login()
    async def captcha(request: Request):
        ...

    @bp.websocket("/websocket")
    class CaptchaWebSocket(WebSocket):
        async def on_ready(self, data: PacketData):
            ...