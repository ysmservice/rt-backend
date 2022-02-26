# RT - Rocation

from sanic.request import Request
from sanic import __app__

from ujson import loads, dumps

from backend import TypedSanic
from backend.utils import CoolDown, api


TABLE = "Rocations"


def on_load(app: TypedSanic):
    @app.route("/api/rocations/gets")
    @CoolDown(7, 10, "リクエストが多すぎます。｜Too many requests.")
    async def page(request: Request):
        async with request.app.ctx.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                assert (page := request.args.get("page")) is not None, "ページが指定されていません。"
                page = int(page)
                assert 1 <= page < 50, "これ以上ページを開けません。"
                page = 9 * page - 9
                must_query = f"language = %s ORDER BY raised DESC LIMIT {page}, 9"
                must_arg = request.args.get("language", "ja")

                if tags := request.args.get("tags"):
                    tags = tags.split(",")
                    assert len(tags) <= 15, (413, "指定したタグが多すぎます。")
                    assert all(len(tag) <= 20 for tag in tags), (413, "タグの文字数が多すぎます。")
                    await cursor.execute(
                        "SELECT * FROM {} WHERE ({}) AND {};".format(
                            TABLE, " ".join(f"tags LIKE %s OR " for _ in tags)[:-4], must_query
                        ), [f"%{tag}%" for tag in tags] + [must_arg]
                    )
                    rows = await cursor.fetchall()
                elif query := request.args.get("search"):
                    assert len(query) <= 100, (413, "文字数が多すぎます。")
                    await cursor.execute(
                        f"SELECT * FROM {TABLE} WHERE (tags LIKE %s OR description LIKE %s OR GuildID = %s) AND {must_query};",
                        (f"%{query}%",)*2+(query, must_arg)
                    )
                    rows = await cursor.fetchall()
                elif query := request.args.get("guild_id"):
                    await cursor.execute(
                        f"SELECT * FROM {TABLE} WHERE GuildID = %s;", (int(query),)
                    )
                    rows = await cursor.fetchall()
                else:
                    await cursor.execute(
                        f"SELECT * FROM {TABLE} WHERE {must_query};",
                        (must_arg,)
                    )
                    rows = await cursor.fetchall()
        return api("Ok", await request.app.ctx.rtc.request(
            "get_rocations", list(filter(lambda row: bool(row), rows))
        ))


    @app.post("/api/rocations/nice/<guild_id:int>")
    @app.ctx.oauth.require_login(True)
    @CoolDown(1, 5, "リクエストが多すぎます。｜Too many requests.")
    async def nice(request: Request, guild_id: int):
        assert request.ctx.user is not None, (403, "ログインをしてください。")
        assert len(request.body) <= 2000, (413, "文字数が多すぎます。")
        async with request.app.ctx.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"SELECT nices FROM {TABLE} WHERE GuildID = %s;", (guild_id,))
                assert (row := await cursor.fetchone()), "サーバーが見つかりませんでした。"
                nices = loads(row[0])
                assert len(nices) < 100, "これ以上Niceできません。"
                nices[str(request.ctx.user.id)] = request.body.decode() or None
                await cursor.execute(
                    f"UPDATE {TABLE} SET nices = %s WHERE GuildID = %s;",
                    (dumps(nices), guild_id)
                )
        return api("Ok", None, 201)

    @app.route("/api/rocations/test/clear/<guild_id:int>", methods=("GET", "POST"))
    async def clear(request: Request, guild_id: int):
        assert request.app.ctx.test, "本番環境ではこれを使うことができません。"
        async with request.app.ctx.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"DELETE FROM {TABLE} WHERE GuildID = %s;", (guild_id,)
                )
        return api("Ok", None, 200)
