# RT.Blueprints - API

from backend import TypedSanic, TypedBlueprint

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


blueprints = (
    testbp, helpbp, short_url_bp, newsbp, oauthbp, captcha_bp, repryptbp,
    guild_bp
)
on_loads = (
    news_on_load, oauth_on_load, captcha_on_load, guild_on_load,
    dashboard_on_load, rocations_on_load
)
bp = TypedBlueprint.group(*blueprints, url_prefix="/api")


def on_load(app: TypedSanic):
    for cbp in blueprints:
        cbp.__class__.app = app
    for on_load_ in on_loads:
        on_load_(app)