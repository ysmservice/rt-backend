# RT.Blueprints - Short URL

from backend import TypedBlueprint, Request
from sanic.response import redirect

from random import choice


HOSTS = ("localhost", "rtbo.tk")
ROUTINE_URLS = (
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=ok7UX3utzvI",
    "https://www.youtube.com/watch?v=lO9alUUIopI",
    "https://www.youtube.com/watch?v=p1pu96oz9Q4",
    "https://www.youtube.com/watch?v=yJ9hikxlGpU",
    "https://www.youtube.com/watch?v=H221MRRgFZs",
    "https://www.youtube.com/watch?v=oYVLIB2Nnic",
    "https://www.youtube.com/watch?v=GtWCtIIsfeg",
    "https://www.youtube.com/watch?v=PgKgEVUVLok",
    "https://www.youtube.com/watch?v=g3jCAyPai2Y",
    "https://www.nicovideo.jp/watch/sm39129486",
    "https://www.nicovideo.jp/watch/sm35532135",
    "https://www.nicovideo.jp/watch/sm38936798",
    "https://www.nicovideo.jp/watch/sm14796309",
    "https://www.nicovideo.jp/watch/sm37658498",
    "https://www.nicovideo.jp/watch/sm33175756",
    "https://www.nicovideo.jp/watch/sm36314738",
    "https://www.youtube.com/watch?v=yj1jC0AmxVA",
    "https://www.nicovideo.jp/watch/sm25227811",
    "https://www.nicovideo.jp/watch/sm21894027",
    "https://www.nicovideo.jp/watch/sm21894027",
    "https://www.youtube.com/watch?v=a-nTCawDhII"
)


bp = TypedBlueprint("ShortURL")


@bp.route("/<custom>", host=HOSTS[1])
async def short_url(request: Request, custom: str):
    if custom in bp.app.ctx.datas["ShortURL"]:
        if f"http://{HOSTS[1]}/{custom}" != bp.app.ctx.datas["ShortURL"][custom]:
            return redirect(bp.app.ctx.datas["ShortURL"][custom])
    return redirect(choice(ROUTINE_URLS))