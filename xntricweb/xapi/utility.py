from typing import Optional, get_args, get_origin, Any

from .const import NOT_SPECIFIED, AnyType


def get_origin_args(_type: AnyType) -> tuple[AnyType, tuple[AnyType, ...]]:
    args = get_args(_type)
    if origin := get_origin(_type):
        return origin, args

    if (origin := getattr(_type, "__class__", None)) and origin is not type:
        return origin, args

    return _type, args


def is_any(value: Any, classes: list[Any]):
    return any(value is _class for _class in classes)


def coalesce(
    *args: Any,
    is_not: Optional[list[Any]] = None,
    also_is_not: Optional[list[Any]] = None,
    check_falsey: bool = True,
) -> Any:
    if not is_not:
        is_not = [None, False]

    if also_is_not:
        is_not.extend(also_is_not)

    for arg in args:
        if not is_any(arg, is_not) and (not check_falsey or arg):
            return arg

    return args[-1]
