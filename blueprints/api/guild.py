# RT.Blueprints.API - Guild

from backend import TypedSanic, TypedBlueprint, WebSocket
from backend.utils import DataEvent

from asyncio import sleep, wait_for, TimeoutError as AioTimeoutError


bp = TypedBlueprint("API.Guild")
bp.queues = {}


@bp.websocket("/guild")
class GuildWebSocket(WebSocket):
    async def on_ready(self, _):
        while self.running == "ok" and not bp.queues:
            await sleep(0.01)
        for key, event in list(bp.queues.items()):
            await self.send(f"fetch_{key}", str(event.data))
            try:
                event.set(await wait_for(self.recv(), timeout=1))
            except AioTimeoutError:
                event.set({})
            del bp.queues[key]
        await self.send("on_ready", "")


def on_load(app: TypedSanic):
    async def fetch_guilds(id_):
        bp.queues["guilds"] = DataEvent()
        bp.queues["guilds"].data = id_
        if (data := await bp.queues["guilds"].wait()):
            return data["data"]
    app.ctx.fetch_guilds = fetch_guilds