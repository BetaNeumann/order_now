from typing import Any
from decimal import Decimal

import orjson


JsonObject = dict[str, Any]
JsonList = list[JsonObject]


def default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def loads(data: bytes):
    return orjson.loads(data)


def dumps(data: JsonObject | JsonList | object):
    return orjson.dumps(data, default=default)
