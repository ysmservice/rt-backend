# RT.Blueprints.API - News

from typing import List

from backend import TypedSanic, DatabaseManager, TypedBlueprint
from backend.utils import api

from aiomysql import Pool, Cursor


class DataManager(DatabaseManager):

    TABLE: str = "news"

    def __init__(self, app: TypedSanic):
        self.pool: Pool = app.ctx.pool
        self.app = app
        super().__init__()

    async def get_all(self, cursor: Cursor = None) -> List[tuple]:
        await cursor.execute(
            f"SELECT * FROM {self.TABLE} ORDER BY id ASC;"
        )
        return [row for row in await cursor.fetchall() if row]


bp = TypedBlueprint("API_News")


def on_ready(app: TypedSanic):
    bp.__class__.data = DataManager(app)


def on_load(app: TypedSanic):
    app.ctx.tasks.append(on_ready)


@bp.route("/news/<number:int>",name="news1")
@bp.route("/news",name="news")
async def news(_, number: int = None):
    rows = await bp.data.get_all()
    if number is not None:
        rows = list(rows)
        row = rows[number]
        data = {
            "content": row[2], "date": row[1],
            "status": "ok", "title": row[2][:row[2].find("\n") + 1]
        }
    else:
        data = {
            str(i): [row[2][:row[2].find("\n") + 1], row[1]]
            for i, row in enumerate(rows)
        }
        data["status"] = "ok"
    return api(data["status"], data)