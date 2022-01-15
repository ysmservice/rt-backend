# RT.Blueprints - Short URL

from sanic.response import html

from backend import TypedBlueprint, Request
from data import TEMPLATE_FOLDER


bp = TypedBlueprint("Embed")


@bp.route("/embed")
async def short_url(request: Request):
    return html(await request.app.ctx.env.aiorender(
        f"{TEMPLATE_FOLDER}/others/embed.html", eloop=request.app.loop,
        data=request.args
    ))