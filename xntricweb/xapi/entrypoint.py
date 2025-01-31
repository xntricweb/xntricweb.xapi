from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Optional, Any, Callable, Iterable
from xntricweb.xapi.arguments import Argument

from .const import log

root_entrypoints: list[Entrypoint] = []
root_effects: list[Entrypoint] = []


_NOT_SPECIFIED = object()


@dataclass
class Entrypoint:
    """
    An application entrypoint.
    """

    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    help: Optional[str] = None
    deprecated: Optional[bool] = False
    description: Optional[str] = None
    epilog: Optional[str] = None
    usage: Optional[str] = None
    entrypoint: Optional[Callable] = None
    parent: Optional[Entrypoint] = None
    arguments: Optional[Iterable[Argument]] = None
    entrypoints: Optional[Iterable[Entrypoint]] = None

    def __post_init__(self):
        if self.parent:
            self.parent.add_subentrypoint(self)

        if not self.entrypoints:
            self.entrypoints = []

        if not self.arguments:
            self.arguments = []

        self._init_entrypoint()

    def add_subentrypoint(self, entrypoint):
        if not self.entrypoints:
            self.entrypoints = []

        self.entrypoints.append(entrypoint)

    def generate_call_args(self, params: dict[str, Any]):
        args = []
        kwargs = {}
        for arg in self.arguments:
            value = params.get(arg.name, arg.default)
            arg.generate_call_arg(value, args, kwargs)

        return args, kwargs

    def execute(self, params: dict[str, Any]):
        if not self.entrypoint:
            raise RuntimeError("Entrypoint not ready to execute %s", self)
        arg, kwargs = self.generate_call_args(params)
        return self.entrypoint(*arg, **kwargs)

    def _get_argument(self, name: str | None, index: int):
        if not self.arguments:
            self.arguments = []

        if name is not None:
            for arg in self.arguments:
                if arg.name == name:
                    return arg

        if index >= 0 and index < len(self.arguments):
            return self.arguments[index]

        arg = Argument(name=name, index=index)
        self.arguments.append(arg)
        return arg

    def _init_entrypoint(self):
        if not self.entrypoint:
            return

        spec = inspect.getfullargspec(self.entrypoint)

        if not self.name:
            self.name = self.entrypoint.__name__

        if not self.description:
            self.description = self.entrypoint.__doc__

        # align defauls
        if spec.defaults:
            arg_defaults = [
                *([_NOT_SPECIFIED] * (len(spec.args) - len(spec.defaults))),
                *spec.defaults,
            ]
        else:
            arg_defaults = [_NOT_SPECIFIED] * len(spec.args)
        index = -1

        for index, (name, default) in enumerate(zip(spec.args, arg_defaults)):
            log.debug("setting up positional arg: %s", name)
            arg = self._get_argument(name, index)
            arg.index = index
            arg.name = name
            arg.annotation = spec.annotations.get(name, None)
            if default is _NOT_SPECIFIED:
                arg.required = True
            else:
                arg.default = default
        if spec.varargs:
            index += 1
            arg = self._get_argument(spec.varargs, index)
            arg.vararg = True
            arg.index = index
            arg.name = spec.varargs
            arg.annotation = spec.annotations.get(spec.varargs, None)
            arg.required = False

        if spec.kwonlydefaults:
            for name, default in spec.kwonlydefaults.items():
                arg = self._get_argument(name, -1)
                arg.name = name
                arg.index = None
                arg.default = default
                arg.required = False
                arg.annotation = spec.annotations.get(name, None)

        log.debug("entrypoint ready: %r", self)
