# RT.Blueprints.API - Short URL

from backend import TypedSanic, TypedBlueprint, Request
from backend.utils import api, is_okip, try_loads


bp = TypedBlueprint("API_ShortURL")


@bp.route("/shorturl", methods=["POST"])
@is_okip(bp)
async def update(request: Request):
    bp.app.ctx.datas["ShortURL"] = try_loads(request)
    return api("ok", None)