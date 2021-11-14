# RT.Backend - Backend

from typing import (
    Any, Callable, Coroutine, Literal, Dict, Union, Optional, Sequence
)

from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask_misaka import Misaka

from sanic.exceptions import SanicException
from sanic.errorpages import HTMLRenderer
from sanic.request import Request
from sanic.log import logger
from sanic import response

from websockets import (
    WebSocketServerProtocol, ConnectionClosedOK, ConnectionClosedError
)
from ujson import loads, dumps

from jishaku.functools import executor_function
from os.path import exists, isfile, isdir
from inspect import iscoroutinefunction
from asyncio import AbstractEventLoop
from aiomysql import create_pool
from traceback import format_exc
from sys import argv

from .typed import Datas, TypedSanic, TypedBot, TypedBlueprint, Packet, PacketData, Self
from .utils import cooldown, wrap_html, DEFAULT_GET_REMOTE_ADDR
from .oauth import DiscordOAuth


aioexists = executor_function(exists)
aioisfile = executor_function(isfile)
aioisdir = executor_function(isdir)


def NewSanic(
    bot_args: tuple, bot_kwargs: dict, token: str, reconnect: bool,
    on_setup_bot: Callable[[TypedBot], Any], pool_args: tuple, pool_kwargs: dict,
    template_engine_exts: Sequence[str], template_folder: str, oauth_kwargs: dict,
    *sanic_args, **sanic_kwargs
) -> TypedSanic:
    "RTのためのバックエンドのSanicを取得するための関数です。"
    app: TypedSanic = TypedSanic(*sanic_args, **sanic_kwargs)

    # テンプレートエンジンを用意する。
    app.ctx.env = Environment(
        loader=FileSystemLoader(template_folder),
        autoescape=select_autoescape(template_engine_exts),
        enable_async=True
    )
    app.ctx.env.filters.setdefault(
        "markdown", Misaka(autolink=True)
    )

    async def template(path, keys={}, **kwargs):
        return response.html(
            await app.ctx.env.get_template(path).render_async(**keys), **kwargs
        )
    app.ctx.template = template
    app.ctx.datas = {
        "ShortURL": {}
    }
    app.ctx.tasks = []
    app.ctx.test = argv[-1] != "production"
    del template

    app.ctx.oauth = DiscordOAuth(app, **oauth_kwargs)

    with open("data/ipbans.txt", "r") as f:
        ipbans = f.read()

    @app.listener("before_server_start")
    async def prepare(app: TypedSanic, loop: AbstractEventLoop):
        if not hasattr(app.ctx, "bot"):
            # データベースのプールの準備をする。
            pool_kwargs["loop"] = loop
            app.ctx.pool = await create_pool(*pool_args, **pool_kwargs)
            # Discordのデバッグ用のBotの準備をする。
            bot_kwargs["loop"] = loop
            app.ctx.bot = TypedBot(*bot_args, **bot_kwargs)
            app.ctx.bot.app = app
            app.ctx.bot.pool = app.ctx.pool
            # Botの準備をさせてBotを動かす。
            on_setup_bot(app.ctx.bot)
            loop.create_task(app.ctx.bot.start(token, reconnect=reconnect))
            await app.ctx.bot.wait_until_ready()
            logger.info("Connected to Discord")
            app.ctx.bot.dispatch("on_loop_ready", app)
            # データベースなどの準備用の関数達を実行する。
            for task in app.ctx.tasks:
                task(app)
            del app.ctx.tasks

    @app.listener("after_server_stop")
    async def close(app: TypedSanic, _: AbstractEventLoop):
        # プールとBotを閉じる。
        if not app.ctx.bot.is_cloesd():
            app.ctx.bot.dispatch("close")
            app.ctx.pool.close()
            await app.ctx.bot.close()

    @app.middleware
    @cooldown(app.ctx, 0.3, from_path=True, wrap_html=True)
    async def on_request(request: Request):
        if (not app.ctx.test and request.host == "146.59.153.178"
                and request.scheme not in ("ws", "wss")):
            return wrap_html(
                request, SanicException("生IPアドレスへのアクセスは禁じられています。", 403)
            )
        if DEFAULT_GET_REMOTE_ADDR(request) in ipbans:
            return wrap_html(
                request, SanicException("あなたはこのウェブサイトにアクセスすることができません。", 401)
            )

        # ファイルが見つかればそのファイルを返す。
        # パスを準備する。
        path = request.path
        if path:
            if path[0] != "/":
                path = f"/{path}"
        else:
            path = "/"
        real_path = f"{template_folder}{path}"
        if await aioisdir(real_path[:-1]):
            # もしフォルダならindex.htmlを付け足す。
            real_path += "index.html"
            path += "index.html"

        # もしファイルが存在するならそのファイルを返す。
        if await aioexists(real_path) and await aioisfile(real_path):
            if real_path.endswith(template_engine_exts):
                return await app.ctx.template(path[1:])
            else:
                if real_path.endswith((".mp4", ".mp3", ".wav", ".ogg", ".avi")):
                    return await response.file_stream(real_path)
                else:
                    return await response.file(real_path)

    @app.exception(Exception)
    async def on_exception(request: Request, exception: Exception):
        # 500と501以外のSanicExceptionはエラーが出力されないようにする。
        if not isinstance(exception, SanicException):
            exception = SanicException("内部エラーが発生しました。", 500)
            if app.ctx.test:
                print(format_exc())
        return HTMLRenderer(request, exception, True).full()

    return app


class WebSocket:
    """Botとウェブソケット通信をするためのクラスです。
    これは継承して使用します。

    Examples
    --------
    ```python
    from backend import PacketData

    ...

    @bp.websocket("/ping")
    class WSPing(WebSocket):
        async def ping(self, data: PacketData) -> str:
            "Botからpingという名前のイベントが来たら呼ばれる関数です。"
            print(f"Received ping: {data}")
            return "pong"
    ```
    """

    handlers: Dict[str, Callable[..., Coroutine]] = {}
    request: Request = None
    ws: WebSocketServerProtocol
    app: Optional[TypedSanic] = None
    loop: AbstractEventLoop
    running: Literal["ok", "closed", "error"] = "ok"

    def __init_subclass__(cls):
        for name in dir(cls):
            if (iscoroutinefunction(func := getattr(cls, name))
                    and "data" in func.__code__.co_varnames):
                # クラスに実装されている通信用のイベントハンドラを保存しておく。
                cls.handlers[func.__name__] = func

    def __new__(cls, request, websocket):
        # インスタンスを作り色々準備をしてコルーチンを返す。
        self = super().__new__(cls)
        self.request, self.ws = request, websocket
        self.ws.simple_websocket = self

        if self.app is not None:
            self.app.ctx.bot.add_listener(self.on_close)

        return self._async_call()

    async def send(self, event_type: str, data: Union[str, dict], **kwargs) -> None:
        "Botにデータを送信します。これはイベントハンドラが何か値を返した際に自動で実行されます。"
        data = {"event_type": event_type, "data": data}
        data.update(kwargs)
        return await self._wrap_error(self.ws.send(dumps(data)))

    async def recv(self) -> Optional[Packet]:
        "Botからデータを取得します。内部的に行われるので普通使いません。"
        if (data := await self._wrap_error(self.ws.recv())):
            return loads(data)

    async def _wrap_error(self, coro: Coroutine) -> Union[str, Optional[Packet]]:
        # 接続エラーが起きる可能性のある子ルーチンをtryでラップして実行する関数です。
        try:
            data = await coro
        except ConnectionClosedOK:
            logger.info(f"Disconnected from bot : {self.__class__.__name__}")
            self.running = "closed"
        except ConnectionClosedError:
            logger.warning(
                f"Disconnected from bot due some error : {self.__class__.__name__}"
            )
            self.running = "error"
        else:
            return data

    async def _async_call(self):
        # このWebSocketがBotに接続した際に実行されるルーチン関数です。
        # ループを実行してBotとの通信をします。
        while self.running == "ok":
            data = await self.recv()

            if isinstance(data, dict):
                if hasattr(self, data["event_type"]):
                    # Botからの実行依頼のイベントハンドラが存在するものなら実行する。
                    logger.debug(f"Run {data['event_type']} event : {self.__class__.__name__}")
                    if (return_data := await getattr(self, data["event_type"])(data)):
                        # もし実行したイベントから何か返されたのならそれを送り返す。
                        await self.send(data["event_type"], return_data)
                else:
                    # 存在しないイベントの場合はエラーで切断する。
                    logger.warning(
                        f"Disconnected from bot because bot gave me an event that dosen't exists : {self.__class__.__name__}"
                    )
                    await self.ws.close(1003, "そのイベントが見つかりませんでした。")
            else:
                # もしBotから切断されたならループを抜ける。
                break

    async def close(self, code: int = 1000, reason: str = "") -> None:
        "WebSocketを終了します。"
        self.running = "closed" if code in (1000, 1001) else "error"
        return await self.ws.close(code, reason)

    async def on_close(self):
        await self.close(reason="バックエンドのシャットダウンによる終了です。")