# RT Backend

from discord import Intents, Game
from sanic.log import logger

from importlib import import_module
from ujson import load, dumps
from os import listdir

from data import (
    BLUEPRINTS_FOLDER, COGS_FOLDER, TEMPLATE_FOLDER, TEMPLATE_EXTS, PREFIX, AUTH_PATH
)
from backend import NewSanic, TypedBot, get_import_path


with open(AUTH_PATH, "r") as f:
    secret = load(f)


def on_setup(bot: TypedBot) -> None:
    bot.load_extension("jishaku")
    # Cogを読み込む。
    for name in listdir(COGS_FOLDER):
        if (not name.startswith("_")
                and ("." not in name or name.endswith(".py"))):
            try:
                bot.load_extension(
                    f"{COGS_FOLDER}.{get_import_path(name)}"
                )
            except Exception as e:
                logger.warning(f"Failed to load the extension : {e}")
            else:
                logger.info(f"Loaded extension : {name}")

    @bot.event
    async def on_ready():
        await bot.change_presence(
            activity=Game("Backend")
        )


app = NewSanic(
    (), dict(
        command_prefix=PREFIX, intents=Intents(messages=False), max_messages=100
    ), secret["token"], True, on_setup, (), secret["mysql"], TEMPLATE_EXTS,
    TEMPLATE_FOLDER, secret["oauth"], "RT-Backend", dumps=dumps
)
app.ctx.secret = secret


# Blueprintを読み込む。
for name in listdir(BLUEPRINTS_FOLDER):
    if not name.startswith("_"):
        module = import_module(f"{BLUEPRINTS_FOLDER}.{get_import_path(name)}")
        if hasattr(module, "on_load"):
            module.on_load(app)
        if hasattr(module, "bp"):
            try:
                module.bp.app = app
            except AttributeError:
                pass
            app.blueprint(module.bp)
            logger.info(f"Loaded blueprint : {name}")


app.run(**secret["app"])