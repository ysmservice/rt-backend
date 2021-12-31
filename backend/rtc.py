# RT Blueprints - RT Connection

from typing import TYPE_CHECKING, Literal, Union, Any

from sanic.server.websockets.connection import WebSocketConnection
from sanic.log import logger
from sanic import Blueprint, Request

from .rt_module.src import rtc
from .utils import is_okip

if TYPE_CHECKING:
    ...


bp = Blueprint("rtc")


@bp.websocket("/rtc")
@is_okip(bp)
class RTConnection(rtc.RTConnectionManager):

    COOLDOWN = 0.005
    NAME = "Backend"

    def __init__(self, request: Request, *args, **kwargs):
        super().__init__(self.NAME, request.app.loop)
        request.app.ctx.rtc = self

    def __new__(cls, _, *args, **kwargs):
        self = super().__new__(cls)
        return self.communication(*args, **kwargs)

    def logger(
        self, mode: Union[Literal["info", "debug", "warn", "error"], str], *args, **kwargs
    ) -> Any:
        "ログ出力をします。"
        return getattr(logger, mode)(*args, **kwargs)