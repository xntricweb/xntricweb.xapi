from typing import get_args, get_origin, Any

from .const import NOT_SPECIFIED, AnyType


def get_origin_args(_type: AnyType) -> tuple[AnyType, tuple[AnyType, ...]]:
    args = get_args(_type)
    if origin := get_origin(_type):
        return origin, args

    if (origin := getattr(_type, "__class__", None)) and origin is not type:
        return origin, args

    return _type, args


def coalesce(*args: Any) -> Any:
    for arg in args:
        if arg is not None and arg is not NOT_SPECIFIED:
            return arg

    return args[-1]
