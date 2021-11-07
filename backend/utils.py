# RT.Backend - Utils

from typing import TYPE_CHECKING, Callable, Optional, Union, Any, List

from sanic import response, exceptions

from functools import wraps
from ujson import dumps

if TYPE_CHECKING:
    from .backend import TypedBlueprint


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
    message: str, data: Union[str, dict, None], status: int = 200, **kwargs
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