from typing import get_args, get_origin

from uv import Any
from .const import NOT_SPECIFIED, AnyType


def get_origin_args(_type: AnyType) -> tuple[AnyType, tuple[AnyType, ...]]:
    return get_origin(_type) or getattr(
        _type, "__class__", None
    ) or _type, get_args(_type)


def coalesce(*args: Any) -> Any:
    for arg in args:
        if arg is not None and arg is not NOT_SPECIFIED:
            return arg

    return args[-1]
