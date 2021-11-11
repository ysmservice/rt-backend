# RT.Backend - Utils

from typing import (
    TYPE_CHECKING, Callable, Coroutine, Optional, Union, Any, List, Dict, Tuple
)

from sanic import response, request, exceptions

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
    message: str, data: Union[int, str, list, dict, None],
    status: int = 200, **kwargs
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


DEFAULT_COOLDOWN = "リクエストの速度が速いです！私耐えられません！もうちょっとスローリーにお願いです。{}秒待ってね。"


def cooldown(
    bp: "TypedBlueprint", seconds: Union[int, float], message: Optional[str] = None,
    cache_max: int = 1000, from_path: bool = False
) -> Callable:
    "レートリミットを設定します。"
    message = message or DEFAULT_COOLDOWN
    def decorator(function):
        @wraps(function)
        async def new(request, *args, **kwargs):
            if from_path:
                name = request.path
            else:
                name = function.__name__
            if not hasattr(bp, "_rtlib_cooldown"):
                bp._rtlib_cooldown = {}
            before = bp._rtlib_cooldown.get(
                name, {}
            ).get(request.ip, 0)
            now = time()
            if name not in bp._rtlib_cooldown:
                bp._rtlib_cooldown[name] = {}
            bp._rtlib_cooldown[name][request.ip] = now
            if len(bp._rtlib_cooldown[name]) >= cache_max:
                del bp._rtlib_cooldown[name] \
                    [sorted(
                        bp._rtlib_cooldown[name].items(),
                        key=lambda x: x[1]
                    )[0][0]]
            if now - before < seconds:
                raise exceptions.SanicException(
                    message.format(seconds), 429
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


class CoolDown:
    "細かくレート制限をRouteにかけたい際に使えるデコレータの名を持つクラスです。"

    rate: int
    per: float
    cache_max: int
    message: str
    strict: bool
    max_per: float
    cache: Dict[str, Tuple[int, float]]
    func: Callable[..., Coroutine]

    def __new__(
        cls, rate: int, per: float, message: str = DEFAULT_COOLDOWN,
        cache_max: int = 1000, strict: bool = True, max_per: Optional[float] = None
    ) -> Callable[[Callable[..., Coroutine]], "CoolDown"]:
        self = super().__new__(cls)
        self.rate, self.per, self.strict = rate, per, strict
        self.cache_max, self.message = cache_max, message
        self.max_per = max_per or per * cache_max // 100
        self.cache = {}

        def decorator(func):
            self.func = func
            return wraps(func)(self)

        return decorator

    async def _async_call(self, request, *args, **kwargs):
        before = self.cache.get(request.ip, (0, (now := time()) + self.per))
        self.cache[request.ip] = (
            before[0] + 1, before[1]
        )
        if self.cache[request.ip][1] > now:
            if self.cache[request.ip][0] > self.rate:
                if self.strict and self.cache[request.ip][1] < self.max_per:
                    self.cache[request.ip][1] += self.per
                raise exceptions.SanicException(
                    self.message.format(self.cache[request.ip][1] - now), 429
                )
        else:
            del self.cache[request.ip]
        return await self.func(request, *args, **kwargs)

    def __call__(self, request: request.Request, *args, **kwargs):
        # もしキャッシュが最大数になったのならcacheで一番古いものを削除する。
        if len(self.cache) >= self.cache_max:
            del self.cache[max(list(self.cache.items()), key=lambda _, d: d[1])[0]]
        # 非同期で実行できるようにコルーチン関数を返す。
        return self._async_call(request, *args, **kwargs)