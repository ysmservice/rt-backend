# RT - Rocation

from sanic.response import HTTPResponse, redirect, html
from sanic.request import Request
from sanic import Blueprint, __app__

from backend.utils import CoolDown, api

from data import TEMPLATE_FOLDER


bp = Blueprint("Rocations", "/rocations")
TABLE = "Rocations"


async def row2dict(row: tuple) -> dict:
    return {
        "name": (await __app__.ctx.rtc.request("get_guild", row[0]))["name"],
        "description": row[1], "tags": row[2], "nices": row[3], "invite": row[4],
        "raised": row[5]
    }


@bp.route("/api/gets/<page:int>")
@CoolDown(7, 10)
async def page(request: Request, page: int):
    assert 0 <= page < 50, "これ以上ページを開けません。"
    page = 10 * page - 10
    async with request.app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                f"SELECT * FROM {TABLE} WHERE language = %s ORDER BY raised LIMIT {page}, 10;",
                (request.args.get("language", "ja"),)
            )
            rows = await cursor.fetchall()
    if rows:
        datas = {}
        for row in filter(lambda row: bool(row), rows):
            datas[row[0]] = await row2dict(row)
        return api("Ok", datas)
    else:
        return api("Error", None, 404)