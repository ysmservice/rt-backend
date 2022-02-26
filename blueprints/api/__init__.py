# RT.Blueprints - API

from asyncio import all_tasks, sleep

from psutil import virtual_memory, cpu_percent
from onami.functools import executor_function

from backend import TypedSanic, TypedBlueprint, Request
from backend.utils import api

from .captcha import bp as captcha_bp, on_load as captcha_on_load
from .guild import bp as guild_bp, on_load as guild_on_load
from .oauth import bp as oauthbp, on_load as oauth_on_load
from .news import bp as newsbp, on_load as news_on_load
from .dashboard import on_load as dashboard_on_load
from .rocations import on_load as rocations_on_load
from .short_url import bp as short_url_bp
from .reprypt_api import bp as repryptbp
from .normal import bp as testbp
from .help import bp as helpbp


general = TypedBlueprint("General")
blueprints = (
    testbp, helpbp, short_url_bp, newsbp, oauthbp, captcha_bp, repryptbp,
    guild_bp, general
)
on_loads = (
    news_on_load, oauth_on_load, captcha_on_load, guild_on_load,
    dashboard_on_load, rocations_on_load
)
bp = TypedBlueprint.group(*blueprints, url_prefix="/api")


@executor_function
def process_psutil() -> tuple[float, float]:
    return virtual_memory().percent, cpu_percent(interval=1)


def on_load(app: TypedSanic):
    for cbp in blueprints:
        cbp.__class__.app = app
    for on_load_ in on_loads:
        on_load_(app)

    async def get_backend_status(_):
        await sleep(4)
        return (
            (app.ctx.pool.size, len(all_tasks())),
            await process_psutil()
        )

    app.ctx.rtc.set_event(get_backend_status)


@general.get("status")
async def get_status(request: Request):
    return api("Ok", await request.app.ctx.rtc.request("get_status", None))