# RT.Backend - Typed

from typing import TypedDict, Callable, Union, Dict, List
from types import SimpleNamespace

from sanic import Sanic, Blueprint, response
from sanic_limiter import Limiter
from jinja2 import Environment
from discord.ext import commands

from aiomysql import Pool


class Datas(TypedDict):
    ShortURL: Dict[str, str]


class TypedContext(SimpleNamespace):
    pool: Pool
    bot: "TypedBot"
    env: Environment
    secret: dict
    datas: Datas
    limiter: Limiter
    tasks: List[Callable]

    def template(
        self, path: str, keys: dict = {}, **kwargs
    ) -> response.BaseHTTPResponse:
        ...


class TypedSanic(Sanic):
    ctx: TypedContext


class TypedBot(commands.Bot):
    app: TypedSanic
    pool: Pool


class TypedBlueprint(Blueprint):
    app: TypedSanic


PacketData = Union[dict, str]


class Packet(TypedDict):
    event_type: str
    data: PacketData


class Self(SimpleNamespace):
    app: TypedSanic
    bp: TypedBlueprint
    pool: Pool