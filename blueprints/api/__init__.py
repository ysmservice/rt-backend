# RT.Blueprints - API

from sanic.exceptions import SanicException

from backend import TypedSanic, TypedBlueprint, Request, logger
from backend.utils import api

from .normal import bp as testbp
from .help import bp as helpbp


blueprints = (testbp, helpbp)
bp = TypedBlueprint.group(*blueprints, url_prefix="/api")


def on_load(app: TypedSanic):
    for cbp in blueprints:
        cbp.app = app
        if hasattr(cbp, "on_load"):
            cbp.on_load(app)


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