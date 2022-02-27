# RT Blueprints - RT WebSocket

from typing import Any

from websockets.connection import OPEN
from sanic.log import logger
from sanic import Request

from .rt_module.src.rtws import RTWebSocket
from .utils import is_okip


class ExtendedRTWebSocket(RTWebSocket):

    _real_ws = None

    def log(self, mode: str, *args, **_) -> Any:
        "ログ出力をします。"
        return getattr(logger, mode)(f"[RTWebSocket] {' '.join(map(str, args))}",)

    async def connect(self, _, *__, **___):
        assert self._real_ws is not None, "WebSocketが用意されていません。"
        return self._real_ws

    def is_connected(self) -> bool:
        return self.ws.connection.state == OPEN


def on_load(app):
    app.ctx.app = app

    rtws = app.ctx.rtws = ExtendedRTWebSocket("Backend")
    app.ctx.env.extends["rtws"] = rtws
    async def _logger(*args, **kwargs) -> None:
        return rtws.log(*args, **kwargs)
    rtws.set_event(_logger, "logger")
    rtws.app = app

    @app.websocket("/api/rtws")
    @is_okip(app.ctx)
    async def rtws_connect(_: Request, ws):
        if rtws.ws is not None and rtws.ws.connection.state == OPEN:
            await rtws.close(1001, "再接続されたので切断しました。")
        rtws._real_ws = ws
        return await rtws.start(None, reconnect=False)