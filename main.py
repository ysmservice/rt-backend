# RT Backend

from sanic.log import logger

from importlib import import_module
from ujson import load, dumps
from os import listdir

from data import (
    BLUEPRINTS_FOLDER, TEMPLATE_FOLDER, TEMPLATE_EXTS, AUTH_PATH
)
from backend import NewSanic, TypedBot, get_import_path


with open(AUTH_PATH, "r") as f:
    secret = load(f)


app = NewSanic(
    (), secret["mysql"], TEMPLATE_EXTS,
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
                ...
            app.blueprint(module.bp)
            logger.info(f"Loaded blueprint : {name}")

if __name__ == '__main__':
    app.run(**secret["app"])