# RT.Blueprints.API - Reprypt API

from backend import TypedBlueprint, Request
from backend.utils import cooldown, try_loads, api

from sanic.exceptions import SanicException
from reprypt import encrypt, decrypt


bp = TypedBlueprint("API.Reprypt")


@bp.route("/reprypt", methods=["POST"])
@cooldown(bp, 0.5)
async def reprypt(request: Request):
    if len(request.body) > 10000:
        raise SanicException(
            "データの大きさが大きすぎます。", 413
        )
    data = try_loads(request)
    if all(key in data for key in ("mode", "content", "password")):
        do = encrypt if data["mode"] == "encrypt" else decrypt
        return api(
            "ok", do(data["content"], data["password"])
        )
    else:
        raise SanicException("たりない値があります。")