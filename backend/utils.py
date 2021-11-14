# RT.Backend - Utils

from typing import (
    TYPE_CHECKING, Callable, Coroutine, Optional, Union, Any, List, Dict, Tuple
)

from sanic import response, request, exceptions
from sanic.errorpages import HTMLRenderer

from jishaku.functools import executor_function
from socket import gethostbyname
from ujson import loads, dumps
from functools import wraps
from asyncio import Event
from time import time

if TYPE_CHECKING:
    from .backend import TypedBlueprint, Request


bot_ip = ""
@executor_function
def get_ip(domain: str) -> str:
    return gethostbyname(domain)


def is_okip(bp: "TypedBlueprint", okip: Optional[List[str]] = None) -> Callable[..., Any]:
    "`auth.json`の`okip`にあるIPからじゃないとアクセスを拒否するようにするデコレータです。"
    def decorator(func):
        @wraps(func)
        async def new(request, *args, **kwargs):
            global bot_ip
            ip = DEFAULT_GET_REMOTE_ADDR(request)
            ok = ip in (okip or bp.app.ctx.secret["okip"])
            ok = ok or ip == bot_ip
            if not ok:
                bot_ip = await get_ip("tasuren.f5.si")
                ok = bot_ip == ip
            if ok:
                return await func(request, *args, **kwargs)
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


def wrap_html(
    request: request.Request, exception: exceptions.SanicException
) -> response.HTTPResponse:
    return HTMLRenderer(request, exception, True).full()


DEFAULT_COOLDOWN = "リクエストの速度が速いです！私耐えられません！もうちょっとスローリーにお願いです。{}秒待ってね。"
DEFAULT_GET_REMOTE_ADDR = lambda request: (
    request.ip if request.app.ctx.test else request.headers["cf-connecting-ip"]
)


def cooldown(
    bp: "TypedBlueprint", seconds: Union[int, float], message: Optional[str] = None,
    cache_max: int = 1000, from_path: bool = False, wrap_html: bool = False,
    get_remote_address: Callable[[request.Request], str] = DEFAULT_GET_REMOTE_ADDR
) -> Callable:
    "レートリミットを設定します。"
    message = message or DEFAULT_COOLDOWN
    def decorator(function):
        @wraps(function)
        async def new(request, *args, **kwargs):
            ip = get_remote_address(request)
            if from_path:
                name = request.path
            else:
                name = function.__name__
            if not hasattr(bp, "_rtlib_cooldown"):
                bp._rtlib_cooldown = {}
            before = bp._rtlib_cooldown.get(
                name, {}
            ).get(ip, 0)
            now = time()
            if name not in bp._rtlib_cooldown:
                bp._rtlib_cooldown[name] = {}
            bp._rtlib_cooldown[name][ip] = now
            if len(bp._rtlib_cooldown[name]) >= cache_max:
                del bp._rtlib_cooldown[name] \
                    [sorted(
                        bp._rtlib_cooldown[name].items(),
                        key=lambda x: x[1]
                    )[0][0]]
            if now - before < seconds:
                e = exceptions.SanicException(
                    message.format(seconds), 429
                )
                if wrap_html:
                    return HTMLRenderer(request, e, True).full()
                else:
                    raise e
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
        cache_max: int = 1000, strict: bool = True, max_per: Optional[float] = None,
        get_remote_address: Callable[[request.Request], str] = DEFAULT_GET_REMOTE_ADDR
    ) -> Callable[[Callable[..., Coroutine]], "CoolDown"]:
        self = super().__new__(cls)
        self.rate, self.per, self.strict = rate, per, strict
        self.cache_max, self.message = cache_max, message
        self.max_per = max_per or per * cache_max // 100
        self.cache = {}
        self.get_remote_address = get_remote_address

        def decorator(func):
            self.func = func
            return wraps(func)(self)

        return decorator

    async def _async_call(self, request, *args, **kwargs):
        ip = self.get_remote_address(request)
        before = self.cache.get(ip, (0, (now := time()) + self.per))
        self.cache[ip] = (
            before[0] + 1, before[1]
        )
        if self.cache[ip][1] > now:
            if self.cache[ip][0] > self.rate:
                if self.strict and self.cache[ip][1] < self.max_per:
                    self.cache[ip][1] += self.per
                raise exceptions.SanicException(
                    self.message.format(self.cache[ip][1] - now), 429
                )
        else:
            del self.cache[ip]
        return await self.func(request, *args, **kwargs)

    def __call__(self, request: request.Request, *args, **kwargs):
        # もしキャッシュが最大数になったのならcacheで一番古いものを削除する。
        if len(self.cache) >= self.cache_max:
            del self.cache[max(list(self.cache.items()), key=lambda _, d: d[1])[0]]
        # 非同期で実行できるようにコルーチン関数を返す。
        return self._async_call(request, *args, **kwargs)