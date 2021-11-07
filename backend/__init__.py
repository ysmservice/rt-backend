# RT - Backend

from sanic import exceptions

from .backend import (
    NewSanic, TypedSanic, TypedBot, TypedBlueprint, Self,
    WebSocket, logger, response, Packet, PacketData, Request
)
from . import utils


def get_import_path(filename: str) -> str:
    ".pyの拡張子のファイルならファイル名を返してフォルダの場合はフォルダ名を返す関数です。"
    return filename[:-3] if "." in filename else filename