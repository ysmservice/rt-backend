# RT Blueprints - RT Connection

from typing import Literal, Union, Any, Tuple

from sanic.log import logger
from sanic import Request

from .rt_module.src.rtc import RTConnection
from .utils import is_okip


class ExtendedRTConnection(RTConnection):
    def logger(
        self, mode: Union[Literal["info", "debug", "warn", "error"], str],
        word: str, *args, **kwargs
    ) -> Any:
        "ログ出力をします。"
        return getattr(logger, mode)(f"[RTConnection] {word}", *args, **kwargs)


def on_load(app):
    app.ctx.app = app
    rtc = app.ctx.rtc = ExtendedRTConnection("Backend")
    app.ctx.env.extends["rtc"] = rtc
    async def _logger(data: Tuple[str, str]) -> None:
        return rtc.logger(*data)
    rtc.set_event(_logger, "logger")


    @app.websocket("/api/rtc")
    @is_okip(app.ctx)
    async def rtc_connect(_: Request, ws):
        rtc.set_loop(app.loop)
        if rtc.connected:
            await rtc.ws.close()
            rtc.ready.clear()
        return await rtc.communicate(ws, True)