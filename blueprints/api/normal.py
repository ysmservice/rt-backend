# RT.Blueprints.API - Normal

from backend import TypedBlueprint, response


bp = TypedBlueprint("api.test")


@bp.route("/ping")
async def ping(_):
    return response.text("pong")