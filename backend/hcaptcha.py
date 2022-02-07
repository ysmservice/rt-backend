# RT.Backend - hCaptcha

from typing import TYPE_CHECKING, Callable, Coroutine, Any, Union, Optional, Tuple

from sanic.exceptions import SanicException, ServiceUnavailable
from sanic.response import HTTPResponse, html
from sanic.request import Request

from reprypt import encrypt, decrypt, convert_hex
from aiohttp import ClientSession
from ujson import loads, dumps
from functools import wraps

if TYPE_CHECKING:
    from .typed import TypedSanic


class hCaptcha:
    def __init__(
        self, app: "TypedSanic", api_key: str, secret_key: str,
        default_template: str, default_sitekey_key: str, default_sitekey: str
    ):
        self.app, self.api_key, self.secret_key = app, api_key, secret_key
        self._session: Optional[ClientSession] = None
        self.default_template = default_template
        self.default_sitekey_key = default_sitekey_key
        self.default_sitekey = default_sitekey

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            self._session = ClientSession(
                loop=self.app.loop, json_serialize=dumps
            )
        return self._session

    async def start(
        self, key: str, data: Union[str, dict], template: Optional[str] = None,
        sitekey_key: Optional[str] = None, sitekey: Optional[str] = None, **kwargs
    ) -> HTTPResponse:
        "hCaptchaを始めるRouteから返すウェブページのテンプレートの特定の言葉を、暗号化した渡されたデータに交換するということをしてくれる関数です。"
        if isinstance(data, dict):
            data = dumps(data)
        keys = {
            key: encrypt(data, self.secret_key, converter=convert_hex),
            sitekey_key or self.default_sitekey_key: sitekey or self.default_sitekey
        }
        keys.update(kwargs)
        return html(await self.app.ctx.env.aiorender(
            template or self.default_template, **keys
        ))

    def end(
        self, extract_data: Callable[..., str] = \
            lambda request, *args, **kwargs: request.args.get("data"),
        check: Callable[[Union[str, dict]], bool] = lambda _: True,
        maybe_json_data: bool = False
    ) -> Callable[
        [Callable[..., Tuple[str, str]]],
        Callable[..., Coroutine[Any, Any, HTTPResponse]]
    ]:
        "hCaptcha認証終了後にリダイレクトされるURLのRouteに付けるべきデコレータです。"
        def decorator(func):
            @wraps(func)
            async def new(request: Request, *args, **kwargs):
                # 暗号化されたデータを解読する。
                data = decrypt(
                    extract_data(request, *args, **kwargs), self.secret_key,
                    converter=convert_hex
                )
                if ((data and data[0] in ("{", "[", '"')
                        and data[-1] in ("}", "]", '"'))
                        and not maybe_json_data):
                    data = loads(data)
                # もしデータが間違っている可能性があるのならエラーをする。
                if check(data):
                    request.ctx.data = data
                else:
                    raise SanicException(
                        "渡された情報の整合性確認に失敗しました。"
                    )
                # 認証を成功したかどうかを取得する。
                async with self.session.post(
                    "https://hcaptcha.com/siteverify", data={
                        "secret": self.api_key,
                        "response": request.form.get("h-captcha-response")
                    }
                ) as r:
                    request.ctx.success = (await r.json(loads=loads))["success"]

                return await func(request, *args, **kwargs)
            return new
        return decorator
