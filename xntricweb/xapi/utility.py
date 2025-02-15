from .const import NOT_SPECIFIED


def _get_origin_args(type):
    if hasattr(type, "__origin__"):
        return type.__origin__, type.__args__

    if not hasattr(type, "__bases__") and hasattr(type, "__args__"):
        return type.__class__, type.__args__

    return type, None


def coalesce(*args):
    for arg in args:
        if arg is not None and arg is not NOT_SPECIFIED:
            return arg

    return args[-1]
