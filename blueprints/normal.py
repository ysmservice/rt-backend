# RT.Blueprints - Normal

from sanic import response, request

from utils import TypedBlueprint


bp = TypedBlueprint("Normal")


@bp.route("/ping")
async def ping(_):
    return response.text("pong")