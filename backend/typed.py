# RT.Backend - Typed

from typing import TypedDict, Union
from types import SimpleNamespace

from sanic import Sanic, Blueprint, response
from discord.ext import commands
from jinja2 import Environment

from aiomysql import Pool


class TypedContext(SimpleNamespace):
    pool: Pool
    bot: "TypedBot"
    env: Environment
    secret: dict

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