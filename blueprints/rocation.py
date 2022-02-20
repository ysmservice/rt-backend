# RT - Rocation

from sanic.response import redirect, html, json
from sanic.request import Request
from sanic import Blueprint, __app__

from data import TEMPLATE_FOLDER


HOST = "localhost" if __app__.ctx.test else "rocations.rt-bot.com"
bp = Blueprint("Rocations", "/rocaltest" if __app__.ctx.test else "", host=HOST)


@bp.route("/")
async def index(request: Request):
    return html(await request.app.ctx.miko.aiorender(f"{TEMPLATE_FOLDER}/rocations/index.html"))


@bp.route("/<path:path>")
async def path(request: Request, path):
    return html(await request.app.ctx.miko.aiorender(f"{TEMPLATE_FOLDER}/rocations/{path}"))


@bp.route("/api/gets/<page:int>")
async def page(request: Request, page: int):
    assert 0 <= page < 50, "これ以上ページを開けません。"
    return json(await request.app.ctx.rtc.request("get_rocations", page))