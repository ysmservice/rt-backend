# RT.Backend - Backend

from typing import (
    Any, Callable, Coroutine, Literal, Dict, Union, Optional, Sequence
)

from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask_misaka import Misaka

from sanic.blueprint_group import BlueprintGroup
from sanic.request import Request
from sanic.log import logger
from sanic import response

from websockets import (
    WebSocketServerProtocol, ConnectionClosedOK, ConnectionClosedError
)
from ujson import loads, dumps

from asyncio import AbstractEventLoop
from jishaku.functools import executor_function
from os.path import exists, isfile, isdir
from inspect import iscoroutinefunction
from aiomysql import create_pool

from .typed import Datas, TypedSanic, TypedBot, TypedBlueprint, Packet, PacketData, Self


aioexists = executor_function(exists)
aioisfile = executor_function(isfile)
aioisdir = executor_function(isdir)


def NewSanic(
    bot_args: tuple, bot_kwargs: dict, token: str, reconnect: bool,
    on_setup_bot: Callable[[TypedBot], Any], pool_args: tuple, pool_kwargs: dict,
    template_engine_exts: Sequence[str], template_folder: str,
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
    del template

    @app.listener("before_server_start")
    async def prepare(app: TypedSanic, loop: AbstractEventLoop):
        # データベースのプールの準備をする。
        pool_kwargs["loop"] = loop
        app.ctx.pool = await create_pool(*pool_args, **pool_kwargs)
        # Discordのデバッグ用ののBotの準備をする。
        bot_kwargs["loop"] = loop
        app.ctx.bot = TypedBot(*bot_args, **bot_kwargs)
        app.ctx.bot.app = app
        app.ctx.bot.pool = app.ctx.pool
        # Botの準備をさせてBotを動かす。
        on_setup_bot(app.ctx.bot)
        loop.create_task(app.ctx.bot.start(token, reconnect=reconnect))
        await app.ctx.bot.wait_until_ready()
        logger.info("Connected to Discord")

    @app.listener("after_server_stop")
    async def close(app: TypedSanic, _: AbstractEventLoop):
        # プールとBotを閉じる。
        app.ctx.pool.close()
        await app.ctx.bot.close()

    @app.middleware
    async def on_request(request: Request):
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
                return await response.file(real_path)

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
    blueprint: Union[TypedBlueprint, BlueprintGroup]
    app: Optional[TypedSanic]
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

        if hasattr(self, "blueprint") and hasattr(self.blueprint, "app"):
            self.app = self.blueprint.app
        else:
            self.app = None

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
                    # 存在しないイベントの場合は
                    logger.warning(
                        f"Disconnected from bot because bot gave me an event that dosen't exists : {self.__class__.__name__}"
                    )
                    await self.ws.close(1003, "そのイベントが見つかりませんでした。")
            else:
                # もしBotから切断されたならループを抜ける。
                break

    async def close(self, code: int = 1000, reason: str = "") -> None:
        "WebSocketを終了します。"
        self.running = "closed" if code in self.running else "error"
        return await self.ws.close(code, reason)

    def __del__(self):
        self.running = "ok"
