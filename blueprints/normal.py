# RT.Blueprints - Normal

from sanic import response

from backend import TypedBlueprint, WebSocket, PacketData, logger


bp = TypedBlueprint("Normal")


@bp.route("/ping")
async def ping(_):
    return response.text("pong")


@bp.websocket("/wstest")
class WSPing(WebSocket):

    blueprint = bp

    async def ping(self, data: PacketData) -> str:
        logger.debug(f"Received ping: {data}")
        return "pong"

    async def print(self, data: PacketData) -> None:
        logger.info(f"WebSocket Test Print: {data}")