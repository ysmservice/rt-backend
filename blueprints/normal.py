# RT.Blueprints - Normal

from sanic import response

from backend import TypedBlueprint, WebSocket, PacketData, logger


bp = TypedBlueprint("Normal")


@bp.websocket("/ping")
class WSPing(WebSocket):
    async def ping(self, data: PacketData) -> str:
        logger.debug(f"Received ping: {data}")
        return "pong"
