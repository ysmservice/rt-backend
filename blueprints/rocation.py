# RT - Rocation

from sanic.request import Request
from sanic import Blueprint, __app__

from ujson import loads, dumps

from backend.utils import CoolDown, api


bp = Blueprint("Rocations", "/rocations")
TABLE = "Rocations"


async def row2dict(row: tuple) -> dict:
    data = await __app__.ctx.rtc.request("get_guild", row[0])
    return {
        "name": data["name"], "icon": data["avatar_url"],
        "description": row[1], "tags": loads(row[2]), "nices": loads(row[3]), "invite": row[4],
        "raised": row[5]
    }


@bp.route("/api/gets/<page:int>")
@CoolDown(7, 10)
async def page(request: Request, page: int):
    assert 1 <= page < 50, "これ以上ページを開けません。"
    page = 9 * page - 9
    async with request.app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                f"SELECT * FROM {TABLE} WHERE language = %s ORDER BY raised LIMIT {page}, 9;",
                (request.args.get("language", "ja"),)
            )
            rows = await cursor.fetchall()
    if rows:
        datas = {}
        for row in filter(lambda row: bool(row), rows):
            datas[row[0]] = await row2dict(row)
        for i in range(8):
            datas[i]  ={
            "name": "RTサーバー",
            "description": """VALORANTでランクやカスタムに一緒に行くフレンド欲しくないですか？
そんな思いでサーバーを作成しました！
😆活発なサーバーになるように盛り上げていきましょう！

【募集対象】
・🔰初心者から上級者まで（オーナーはゴールド帯です）
・今上手くなくても、上手くなっていきたい方
・♂♀性別・年齢関係なし

【特徴】
・bot導入により快適な利用ができます。😁 さらに快適に使用できるよう要望もお待ちしております。
・ランクごとにチャンネルが分かれているので、同じランクの方と交流しやすいです（人が増えればw）🤝
・雑談チャンネルもあるので、プレイに疲れたらおしゃべりしましょう！
・女性メンバーも在籍し、活発に活動しています！

【参加NG（No participation）】
・ルールを守れない方
・人が嫌がることをする方
・日本語が話せない方（Those who do not speak Japanese.）
・ランクでスマーフ（自分の最高ランクより下のランクでプレイ）する方、またそれを推奨している方""",
            "tags": [chr(x) for x in range(78+3*i-3, 78+3*i)],
            "nices": [],
            "invite": "https://discord.gg/vPygd4UJnf",
            "raised": 1645520000
        }
        return api("Ok", datas)
    else:
        return api("Error", None, 404)