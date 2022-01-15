# RT.Blueprints.API - Captcha

from urllib.parse import unquote
from os.path import exists
from os import listdir
from time import time

from sanic.response import html

from aiofiles.os import remove as aioremove, wrap
from aiofiles import open as aioopen
from reprypt import decrypt

from backend import TypedSanic, TypedBlueprint, Request, hCaptcha
from backend.utils import CoolDown, is_okip, api

from data import TEMPLATE_FOLDER


bp = TypedBlueprint("API.Captcha", "captcha")
TIMEOUT = 300
COOLDOWN = "クールダウン中です。{}秒後にもう一度お試しください。"
aioexists = wrap(exists)
aiolistdir = wrap(listdir)


def on_load(app: TypedSanic):
    captcha = hCaptcha(
        app, app.ctx.secret["hCaptcha"]["test" if app.ctx.test else "production"],
        app.ctx.secret["secret_key"], f"{TEMPLATE_FOLDER}/captcha.html", "sitekey",
        "20000000-ffff-ffff-ffff-000000000002" if app.ctx.test
        else "0a50268d-fa1e-405f-9029-710309aad1b0"
    )

    @app.route("/captcha")
    @CoolDown(4, 10, COOLDOWN)
    async def captcha_first(request: Request):
        return await captcha.start(
            "session", {
                "data": unquote(request.args.get("session")),
                "timeout": time() + 120
            }, redirect_url="/captcha/end"
        )

    @app.route("/captcha/end", methods=["POST"])
    @CoolDown(2, 10, COOLDOWN)
    @captcha.end(check=lambda data: data["timeout"] > time())
    async def captcha_end(request: Request):
        return html(await app.ctx.env.aiorender(
            f"{TEMPLATE_FOLDER}/captcha_result.html",
            result="認証に成功しました。以下のコードをDiscordで選択してください。"
                if request.ctx.success else "認証に失敗しました。もう一度五秒後に挑戦してください。",
            code=decrypt(request.ctx.data["data"], app.ctx.secret["normal_secret_key"])
                if request.ctx.success else "Failed..."
        ))

    @bp.post("/image/post")
    @is_okip(bp)
    async def captcha_image_post(request: Request):
        async with aioopen(
            f"{TEMPLATE_FOLDER}/{request.args.get('path')}", "wb"
        ) as f:
            await f.write(request.files["file"][0].body)
        return api("Ok", None, 201)

    @bp.post("/image/delete")
    @is_okip(bp)
    async def captcha_image_delete(request: Request):
        if await aioexists(path := f"{TEMPLATE_FOLDER}/{request.body.decode()}"):
            await aioremove(path)
        return api("Ok", None)

    @app.signal("server.shutdown.before")
    async def on_close(app, loop):
        for filename in await aiolistdir(f"{TEMPLATE_FOLDER}/data/captcha"):
            if filename.endswith(".png"):
                await aioremove(f"{TEMPLATE_FOLDER}/data/captcha/{filename}")
