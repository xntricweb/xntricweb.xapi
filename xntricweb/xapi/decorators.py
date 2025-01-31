from typing import Callable
from .entrypoint import Entrypoint, root_entrypoints, root_effects
from .arguments import Argument


def effect(
    entrypoint: Entrypoint | Callable | str | None = None,
    *,
    deprecated=False,
    **kwargs,
):
    def wrap(fn: Callable):
        _entrypoint = Entrypoint(entrypoint=fn, **kwargs)

        if not _entrypoint.parent:
            root_effects.append(_entrypoint)

        return _entrypoint

    kwargs["deprecated"] = deprecated

    if isinstance(entrypoint, Entrypoint):
        kwargs["parent"] = entrypoint
        entrypoint = None

    elif isinstance(entrypoint, str):
        kwargs["name"] = entrypoint

    elif isinstance(entrypoint, Callable):
        return wrap(entrypoint)

    return wrap


def entrypoint(
    entrypoint: Entrypoint | Callable | str | None = None,
    *,
    deprecated=False,
    **kwargs,
):
    def wrap(fn: Callable):
        _entrypoint = Entrypoint(entrypoint=fn, **kwargs)

        if not _entrypoint.parent:
            root_entrypoints.append(_entrypoint)

        return _entrypoint

    kwargs["deprecated"] = deprecated

    if isinstance(entrypoint, Entrypoint):
        kwargs["parent"] = entrypoint
        entrypoint = None

    elif isinstance(entrypoint, str):
        kwargs["name"] = entrypoint

    elif isinstance(entrypoint, Callable):
        return wrap(entrypoint)

    return wrap
