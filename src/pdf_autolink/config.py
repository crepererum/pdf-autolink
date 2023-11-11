from __future__ import annotations

from dataclasses import dataclass
import tomllib
from typing import TypeAlias

JSON_DICT: TypeAlias = dict[str, "JSON"]
JSON_LIST: TypeAlias = list["JSON"]
JSON: TypeAlias = JSON_DICT | JSON_LIST | str | int | float | bool | None


def load_config(file: str) -> Config:
    cfg = {}
    if file:
        with open(file, "rb") as fp:
            cfg = tomllib.load(fp)

    return Config(**cfg)


@dataclass
class Config:
    passes: dict[str, JSON_DICT] | None = None
