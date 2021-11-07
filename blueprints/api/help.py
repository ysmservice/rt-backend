# RT.BLueprints.API - Help

from sanic.exceptions import SanicException

from ujson import loads

from backend import TypedBlueprint, Self, Request
from backend.utils import api, is_okip, try_loads


bp = TypedBlueprint("API.Help")
me = Self(bp=bp)
me.data = {}


def on_load(app):
    me.app = app


CATEGORIES = {
    "bot": "RT",
    "server-tool": "ServerTool",
    "server-panel": "ServerPanel",
    "server-safety": "ServerSafety",
    "server-useful": "ServerUseful",
    "entertainment": "Entertainment",
    "individual": "Individual",
    "chplugin": "ChannelPlugin",
    "music": "Music",
    "other": "Other"
}


@bp.route("/help")
async def help(request: Request):
    return api("ok", me.data)


@bp.route("/help/get/<category>/<command_name>")
@bp.route("/help/get/<category>")
async def get(request: Request, category: str, command_name: str = ""):
    category = CATEGORIES.get(category, category)
    lang = "ja"
    if command_name:
        data = {"g-title": category, "status": "Not found"}
        data["content"] = (
            f"# {command_name}\n"
            + me.data[category][command_name][lang][1]
                .replace("### ", "## ")
            if command_name in me.data.get(category, {})
            else ".0.エラー：見つかりませんでした。"
        )
        if not data["content"].startswith(".0.") and data["content"]:
            data["status"] = "ok"
    else:
        count = 0
        data = {
            str(count := count + 1):[
                key, me.data[category][key][lang][0]
            ]
            for key in me.data[category]
        } if category in me.data else {}
        data["status"] = "ok" if data else "Not found"
        data["title"] = category
    return api(data["status"], data, 200 if data["status"] == "ok" else 404)


@bp.route("/help/update", methods=["POST"])
@is_okip(bp)
async def update(request: Request):
    me.data = try_loads(request)
    return api("ok", None)