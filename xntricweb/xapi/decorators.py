from typing import Any, Callable, Optional
from .entrypoint import Entrypoint, root_entrypoints, root_effects


def effect(
    entrypoint: Optional[Entrypoint | Callable[..., Any] | str] = None,
    *,
    deprecated: bool = False,
    **kwargs: Any,
):
    def wrap(fn: Callable[..., Any]):
        _entrypoint = Entrypoint.from_function(fn, **kwargs)
        # _entrypoint = Entrypoint(entrypoint=fn, **kwargs)

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
    entrypoint: Entrypoint | Callable[..., Any] | str | None = None,
    *,
    deprecated: bool = False,
    **kwargs: Any,
):
    def wrap(fn: Optional[Callable[..., Any]] = None):
        if fn:
            _entrypoint = Entrypoint.from_function(fn, **kwargs)
        else:
            _entrypoint = Entrypoint(**kwargs)

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
