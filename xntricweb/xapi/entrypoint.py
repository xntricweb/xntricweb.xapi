from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Optional, Any, Callable, Iterable
from xntricweb.xapi.arguments import Argument
from .const import NOT_SPECIFIED
from .const import log

root_entrypoints: list[Entrypoint] = []
root_effects: list[Entrypoint] = []


@dataclass
class Entrypoint:
    """
    An application entrypoint.
    """

    name: Optional[str] = None
    aliases: Optional[list[str]] = None
    help: Optional[str] = None
    deprecated: Optional[bool] = None
    description: Optional[str] = None
    epilog: Optional[str] = None
    usage: Optional[str] = None
    entrypoint: Optional[Callable] = None
    parent: Optional[Entrypoint] = None
    arguments: Optional[Iterable[Argument]] = None
    entrypoints: Optional[Iterable[Entrypoint]] = None

    @property
    def has_required_arguments(self):
        return any([arg.required for arg in self.arguments])

    def __key(self):
        return (
            self.name,
            self.aliases,
            self.help,
            self.deprecated,
            self.description,
            self.epilog,
            self.usage,
            self.entrypoint,
            self.parent,
            self.arguments,
            self.entrypoints,
        )

    def __hash__(self):
        return hash(self.__key)

    def __eq__(self, other):
        if hasattr(other, "__key"):
            return self.__key == other.__key

    def __post_init__(self):

        if not self.entrypoints:
            self.entrypoints = []

        if not self.arguments:
            self.arguments = []

        if self.parent:
            self.parent.add_subentrypoint(self)

        if self.__class__ is not Entrypoint:
            self._init_subclass()

        assert self.name or self.entrypoint, "name or entrypoint are required"

    def _init_subclass(self):
        log.debug("initializing subclass %r", self.__class__.__name__)
        if not self.name:
            self.name = self.__class__.__name__.lower()

        include = getattr(self, "_include_entries_", None)
        exclude = getattr(self, "_exclude_entries_", [])
        exclude.extend(dir(Entrypoint))

        log.debug("method inclusions: %r", include)
        log.debug("method exclusions: %r", exclude)

        if include:
            for name in include:
                if name not in exclude:
                    self._init_subentrypoint(name)
            return

        for name in dir(self):
            if name[0] != "_" and name not in exclude:
                self._init_subentrypoint(name)
            else:
                log.debug("exclude potential entrypoint %r", name)

    def _init_subentrypoint(self, name):
        log.debug("initializing sub entypoint: %r", name)
        fn = getattr(self, name)
        subentrypoint = self.from_function(fn)
        self.add_subentrypoint(subentrypoint)

    def add_subentrypoint(self, entrypoint):
        assert (
            not self.has_required_arguments
        ), "Entrypoint with required params cannot be used as parents"

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

    def execute(self, params: dict[str, Any], executor):
        if self.parent:
            self.parent.execute(params)

        if not self.entrypoint:
            raise AttributeError(
                "Nothing to do for entrypoint: %s" % self.name
            )

        arg, kwargs = self.generate_call_args(params)
        return self.entrypoint(*arg, **kwargs)

    def _get_argument(self, name: str | None, index: int):
        if not self.arguments:
            self.arguments = []

        if index >= 0 and index < len(self.arguments):
            return self.arguments[index]

        if name is not None:
            for arg in self.arguments:
                if arg.name == name:
                    return arg

        arg = Argument(name=name, index=index)
        self.arguments.append(arg)
        return arg

    @staticmethod
    def from_function(fn, **overrides):
        details = _get_fn_details(fn)
        spec = inspect.signature(fn)
        return Entrypoint(
            entrypoint=fn,
            arguments=[
                Argument(**info)
                for info in _get_inspect_arg_details(spec.parameters.values())
            ],
            **(details | overrides),
        )

    def __str__(self):
        return f"entrypoint({self.name})"

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join([
            f'{k}={v}'
            for k, v in vars(self).items()
            if not (v is None or v is NOT_SPECIFIED or k[0] == ('_'))
        ])})"


def _get_inpect_arg_detail(index, param: inspect.Parameter):

    detail = _make_detail(
        index=(
            index
            if param.kind
            in (
                param.POSITIONAL_ONLY,
                param.POSITIONAL_OR_KEYWORD,
                param.VAR_POSITIONAL,
            )
            else None
        ),
        name=param.name,
        annotation=(
            (param.annotation if param.annotation is not param.empty else None)
            or (
                (
                    param.default
                    and param.default is not param.empty
                    and param.default is not NOT_SPECIFIED
                    and type(param.default)
                )
            )
            or None
        ),
        default=(
            param.default
            if param.default is not param.empty
            else NOT_SPECIFIED
        ),
        vararg=(
            (
                param.kind is param.VAR_KEYWORD
                or param.kind is param.VAR_POSITIONAL
            )
            or None
        ),
    )
    log.debug("generated argument detail: %s", detail)
    return detail


def _get_fn_details(fn: Callable):
    return {
        "name": (
            fn.__name__ if hasattr(fn, "__name__") else fn.__class__.__name__
        ),
        "description": fn.__doc__,
    }


def _get_inspect_arg_details(params: list[inspect.Parameter]):

    return [
        _get_inpect_arg_detail(index, param)
        for index, param in enumerate(params)
    ]

    # for param in params:
    #     if param.kind is param.POSITIONAL_ONLY:
    #         log.debug("setting up positional arg: %s", param.name)
    #         details


def _make_detail(**kwargs):
    return {
        n: v
        for n, v in kwargs.items()
        if not ((n != "default" and v is None) or v is NOT_SPECIFIED)
    }
