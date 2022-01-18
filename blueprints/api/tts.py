# RT.Blueprints.API - TTS

from typing import Dict

from sanic.exceptions import ServiceUnavailable
from sanic.response import file_stream

from jishaku.functools import executor_function
from aiofiles import open as async_open
from aiofiles.os import remove
from base64 import decodebytes
from os.path import exists
import asyncio

from backend import TypedBot, TypedBlueprint, Request, WebSocket, Self, PacketData
from backend.utils import api, is_okip, try_loads
from data import TEMPLATE_FOLDER


bp = TypedBlueprint("API_TTS", "/tts")
aioexists = executor_function(exists)
class TypedSelf(Self):
    queue: asyncio.Queue
    bot: TypedBot
    datas: Dict[str, asyncio.Event] = {}
    ws: "RoutineLoader"
me = TypedSelf()


def on_ready(app):
    me.bot = app.ctx.bot


def on_load(app):
    app.ctx.tasks.append(on_ready)


@bp.websocket("/routine/loader")
@is_okip(bp)
class RoutineLoader(WebSocket):
    async def ready(self, _):
        me.queue = asyncio.Queue(loop=self.loop)
        me.ws = self
        while not me.bot.is_closed():
            try:
                data = me.queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)
            else:
                await self.send("load", data)
                me.queue.task_done()
                await self.recv()
                me.datas[data].set()


@bp.route("/routine/post", methods=["POST"])
@is_okip(bp)
async def routine_post(request: Request):
    data = try_loads(request)
    async with async_open(
        f"{TEMPLATE_FOLDER}/data/routine/{data['filename']}", "wb"
    ) as f:
        await f.write(decodebytes(data["data"].encode()))
    return api("ok", None)


@bp.route("/routine/delete", methods=["POST"])
@is_okip(bp)
async def routine_delete(request: Request):
    for filename in try_loads(request)["files"]:
        await remove(f"{TEMPLATE_FOLDER}/data/routine/{filename}")
    return api("ok", None)


@bp.route("/routine/get/<filename>")
@is_okip(bp)
async def routine(request: Request, filename: str):
    if hasattr(me, "ws"):
        path = f"{TEMPLATE_FOLDER}/data/routine/{filename}"
        if not await aioexists(path):
            me.datas[filename] = asyncio.Event(loop=request.app.loop)
            await me.queue.put(filename)
            await me.datas[filename].wait()
        return await file_stream(path)
    else:
        raise ServiceUnavailable("まだ準備ができていないので何も返せません。")