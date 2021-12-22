# RT.Blueprints.API - Captcha

from backend import TypedSanic, TypedBlueprint, Request, hCaptcha
from backend.utils import CoolDown, is_okip, api

from aiofiles.os import remove as aioremove
from aiofiles import open as aioopen
from reprypt import decrypt
from time import time

from data import TEMPLATE_FOLDER


bp = TypedBlueprint("API.Captcha", "captcha")
TIMEOUT = 300
COOLDOWN = "クールダウン中です。{}秒後にもう一度お試しください。"


def on_load(app: TypedSanic):
    captcha = hCaptcha(
        app, app.ctx.secret["hCaptcha"]["test" if app.ctx.test else "production"],
        app.ctx.secret["secret_key"], "captcha.html", "sitekey",
        "20000000-ffff-ffff-ffff-000000000002" if app.ctx.test
        else "0a50268d-fa1e-405f-9029-710309aad1b0"
    )

    @app.route("/captcha")
    @CoolDown(4, 10, COOLDOWN)
    @app.ctx.oauth.require_login()
    async def captcha_first(request: Request):
        return await captcha.start(
            "session", request.args.get("session"), redirect_url="/captcha/end"
        )

    @app.route("/captcha/end", methods=["POST"])
    @CoolDown(2, 10, COOLDOWN)
    @captcha.end(check=lambda data: data["timeout"] > time())
    async def captcha_end(request: Request):
        return await app.ctx.template(
            "captcha_result.html", keys={
                "result": "認証に成功しました。以下のコードをDiscordで選択してください。"
                    f"<br><code>{decrypt(request.ctx.data, app.ctx.secret['normal_secret_key'])}</code>"
                    if request.ctx.success else "認証に失敗しました。もう一度五秒後に挑戦してください。"
            }
        )

    @bp.post("/image/post")
    @is_okip(bp)
    async def captcha_image_post(request: Request):
        async with aioopen(f"{TEMPLATE_FOLDER}/{app.ctx}") as f:
            await f.write(request.body)
        return api("Ok", None, 201)

    @bp.post("/image/delete")
    @is_okip(bp)
    async def captcha_image_delete(request: Request):
        await aioremove(f"{TEMPLATE_FOLDER}/{request.body.decode()}")
        return api("Ok", None)