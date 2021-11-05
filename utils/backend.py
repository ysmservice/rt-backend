# RT.Utils - Backend

from typing import Callable, Any, Sequence

from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask_misaka import Misaka

from sanic.request import Request
from sanic.log import logger
from sanic import response

from jishaku.functools import executor_function
from os.path import exists, isfile, isdir
from asyncio import AbstractEventLoop
from aiomysql import create_pool

from .typed import TypedSanic, TypedBot, TypedBlueprint


aioexists = executor_function(exists)
aioisfile = executor_function(isfile)
aioisdir = executor_function(isdir)


def NewSanic(
    bot_args: tuple, bot_kwargs: dict, token: str, reconnect: bool,
    on_setup_bot: Callable[[TypedBot], Any], pool_args: tuple, pool_kwargs: dict,
    template_engine_exts: Sequence[str], template_folder: str,
    *sanic_args, **sanic_kwargs
) -> TypedSanic:
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