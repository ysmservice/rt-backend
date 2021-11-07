# RT.Blueprints - API

from backend import TypedSanic, TypedBlueprint

from .test import bp as testbp


blueprints = (testbp,)
bp = TypedBlueprint.group(*blueprints, url_prefix="/api")


def on_load(app: TypedSanic):
    for cbp in blueprints:
        cbp.app = app