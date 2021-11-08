# RT.Backend - Utils

from typing import TYPE_CHECKING, Callable, Optional, Union, Any, List

from sanic import response, exceptions

from ujson import loads, dumps
from functools import wraps
from asyncio import Event
from time import time

if TYPE_CHECKING:
    from .backend import TypedBlueprint, Request


def is_okip(bp: "TypedBlueprint", okip: Optional[List[str]] = None) -> Callable[..., Any]:
    "`auth.json`の`okip`にあるIPからじゃないとアクセスを拒否するようにするデコレータです。"
    def decorator(func):
        @wraps(func)
        async def new(request, *args, **kwargs):
            if request.ip in (okip or bp.app.ctx.secret["okip"]):
                return await func(request, *args, **kwargs)
            else:
                raise exceptions.Unauthorized(
                    "アクセス許可IPリストにあなたのIPがないので処理ができませんでした。"
                )
        return new
    return decorator


def api(
    message: str, data: Union[int, str, list, dict, None], status: int = 200, **kwargs
) -> response.HTTPResponse:
    "API用のレスポンスを返します。"
    kwargs["dumps"] = dumps
    kwargs["status"] = status
    return response.json(
        {
            "status": kwargs["status"],
            "message": message,
            "data": data
        }, **kwargs
    )


def try_loads(request: "Request") -> Union[dict, list, str]:
    try:
        return loads(request.body)
    except ValueError:
        raise exceptions.SanicException("データが正しくありません。", 400)


def cooldown(bp: "TypedBlueprint", seconds: Union[int, float]):
    "レートリミットを設定します。"
    def decorator(function):
        @wraps(function)
        async def new(request, *args, **kwargs):
            if not hasattr(bp, "_rtlib_cooldown"):
                bp._rtlib_cooldown = {}
            before = bp._rtlib_cooldown.get(
                function.__name__, {}
            ).get(request.ip, 0)
            now = time()
            if function.__name__ not in bp._rtlib_cooldown:
                bp._rtlib_cooldown[function.__name__] = {}
            bp._rtlib_cooldown[function.__name__][request.ip] = now
            if now - before < seconds:
                raise exceptions.SanicException(
                    "Too many request.", 429
                )
            else:
                return await function(request, *args, **kwargs)
        return new
    return decorator


class DataEvent(Event):
    data: Any = None

    def set(self, data: Any):
        self.data = data
        super().set()

    def clear(self):
        self.data = None

    async def wait(self) -> Any:
        await super().wait()
        return self.data