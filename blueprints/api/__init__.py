# RT.Blueprints - API

from sanic.exceptions import SanicException

from backend import TypedSanic, TypedBlueprint, Request, logger
from backend.utils import api

from .dashboard import bp as dashboard_bp, on_load as dashboard_on_load
from .captcha import bp as captcha_bp, on_load as captcha_on_load
from .oauth import bp as oauthbp, on_load as oauth_on_load
from .news import bp as newsbp, on_load as news_on_load
from .tts import bp as ttsbp, on_load as tts_on_load
from .short_url import bp as short_url_bp
from .reprypt_api import bp as repryptbp
from .normal import bp as testbp
from .help import bp as helpbp


blueprints = (
    testbp, helpbp, short_url_bp, newsbp, ttsbp, oauthbp, captcha_bp, repryptbp,
    dashboard_bp
)
on_loads = (
    news_on_load, tts_on_load, oauth_on_load, captcha_on_load, dashboard_on_load
)
bp = TypedBlueprint.group(*blueprints, url_prefix="/api")


def on_load(app: TypedSanic):
    for cbp in blueprints:
        cbp.app = app
    for on_load_ in on_loads:
        on_load_(app)


@bp.exception(Exception)
async def on_error(request: Request, exception: Exception):
    # APIで発生したエラーは辞書に直す。
    status = 200
    if isinstance(exception, SanicException):
        status = exception.status_code
        res = api(exception.message, None, exception.status_code)
    else:
        status = 500
        res = api(str(exception), None, 500)

    if status in (500, 501):
        # もし内部エラーが発生したのならログを出力しておく。
        logger.error(f"Error on {request.path} : {exception}")

    return res