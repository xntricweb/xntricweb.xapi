import argparse
from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
)

from .arguments import Argument, ConversionError
from .entrypoint import Entrypoint

from .const import log, NOT_SPECIFIED
from .utility import _get_origin_args
from .xapi_docstring_parser import DocInfo


@dataclass
class _ParserTranslationContext:
    argument: Argument
    parser_args: List[Any]
    parser_kwargs: Dict[str, Any]

    origin: Optional[Type | UnionType] = None
    origin_params: Optional[Tuple[Type | UnionType]] = None


# entrypoint_parsers: dict[Entrypoint, argparse.ArgumentParser] = {}

_Translator = Callable[[_ParserTranslationContext], bool]


def default_translator(_):
    pass


def literal_translator(ctx: _ParserTranslationContext):

    if len(ctx.origin_params) > 1:
        ctx.parser_kwargs["choices"] = list(ctx.origin_params)
    elif len(ctx.origin_params) == 1:
        raise AttributeError("single Literal option not supported")
    else:
        raise TypeError("Cannot translate empty literal expression.")


def bool_translator(ctx: _ParserTranslationContext):
    state = ctx.argument.default is True
    ctx.parser_kwargs["default"] = state
    ctx.parser_kwargs["action"] = f"store_{str(not state).lower()}"


def list_translator(ctx: _ParserTranslationContext):
    ctx.parser_kwargs["nargs"] = "*"


def tuple_translator(ctx: _ParserTranslationContext):
    if ctx.origin_params:
        ctx.parser_kwargs["nargs"] = len(ctx.origin_params)
    else:
        ctx.parser_kwargs["nargs"] = "*"


def enum_translator(ctx: _ParserTranslationContext):
    enum_choices = [k for k in vars(ctx.origin) if not k[0] == "_"]
    ctx.parser_kwargs["choices"] = enum_choices


def union_translator(ctx: _ParserTranslationContext):
    for type in ctx.origin_params:
        origin, origin_params = _get_origin_args(type)
        sub_ctx = _ParserTranslationContext(
            argument=ctx.argument,
            origin=origin,
            origin_params=origin_params,
            parser_args=[],
            parser_kwargs={},
        )

        _translate(sub_ctx)

        # TODO: check arg compatibility with existing args

        ctx.parser_args.extend(sub_ctx.parser_args)
        ctx.parser_kwargs.update(sub_ctx.parser_kwargs)


_translators = {
    Union: union_translator,
    UnionType: union_translator,
    Literal: literal_translator,
    list: list_translator,
    tuple: tuple_translator,
    bool: bool_translator,
    Enum: enum_translator,
}


def _get_translator(
    origin, default: Optional[_Translator] = None
) -> _Translator | None:
    translator = _translators.get(origin, None)
    if not translator:
        log.debug("searching base translators for origin: %r", origin)
        if not hasattr(origin, "__bases__"):
            log.debug("found %r class for origin %r", origin.__class__, origin)
            origin = origin.__class__

        for base in reversed(origin.__bases__):
            translator = _translators.get(base, None)
            if translator:
                log.debug(
                    "found translator for base %r for origin %r", base, origin
                )
                break

    return translator or default


def _translate(ctx: _ParserTranslationContext):
    if not ctx.origin:
        if ctx.argument.vararg:
            if ctx.argument.index is not None:
                origin = list
                origin_args = (ctx.argument.annotation,)
            else:
                ctx.parser_kwargs["action"] = "store_const"
                ctx.parser_kwargs["const"] = "KWARG"
                # ctx.parser_kwargs["nargs"] = 0
                return
        else:
            origin, origin_args = _get_origin_args(ctx.argument.annotation)
        ctx.origin = origin
        ctx.origin_params = origin_args

    translator = _get_translator(ctx.origin, default_translator)

    log.debug(
        "translating %r argument using translator %r with origin: %r[%r]",
        ctx.argument.name,
        translator.__name__,
        ctx.origin,
        ctx.origin_params,
    )
    translator(ctx)
    log.debug(
        "translated %r argument to parser args: %r, %r",
        ctx.argument.name,
        ctx.parser_args,
        ctx.parser_kwargs,
    )


class XAPI:

    def __init__(self):
        self.effects: list[Entrypoint] = []
        self.entrypoints: list[Entrypoint] = []

    def dashed_name(self, name: str):
        return name.replace("_", "-")

    def entrypoint(
        self,
        entrypoint: (
            Type[Entrypoint] | Entrypoint | Callable | str | None
        ) = None,
        /,
        *,
        deprecated=False,
        **kwargs,
    ):
        log.debug("setting up new entrypoint %r", entrypoint)

        def wrap(fn: Callable | Entrypoint = None):
            if isinstance(fn, Entrypoint):
                log.debug("using previously created entrypoint %r", fn)
                _entrypoint = fn

            elif type(fn) is type and issubclass(fn, Entrypoint):
                log.debug("setting up entrypoint subclass %r", fn)
                _entrypoint = fn(**kwargs)

            elif isinstance(fn, Callable):
                log.debug("building entrypiont from callable: %r", fn)
                _entrypoint = Entrypoint.from_function(fn, **kwargs)
            else:
                log.debug(
                    "not sure what's happening with %r, just using kwargs", fn
                )
                _entrypoint = Entrypoint(**kwargs)

            if not _entrypoint.parent:
                self.entrypoints.append(_entrypoint)

            return _entrypoint

        if deprecated:
            kwargs["deprecated"] = deprecated

        if isinstance(entrypoint, str):
            kwargs["name"] = entrypoint
            entrypoint = None

        if entrypoint:
            return wrap(entrypoint)
        return wrap

    def effect(
        self,
        entrypoint: Entrypoint | Callable | str | None = None,
        *,
        deprecated=False,
        **kwargs,
    ):
        def wrap(fn: Callable):
            _entrypoint = Entrypoint.from_function(fn, **kwargs)
            # _entrypoint = Entrypoint(entrypoint=fn, **kwargs)

            if not _entrypoint.parent:
                self.effects.append(_entrypoint)

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

    def run(
        self,
        argv: list[str] | None = None,
        namespace: argparse.Namespace | None = None,
        effect_parser: argparse.ArgumentParser | None = None,
        root_parser: argparse.ArgumentParser | None = None,
        **parser_args,
    ):
        if not effect_parser:
            effect_parser = argparse.ArgumentParser(add_help=False)

        if not root_parser:
            root_parser = argparse.ArgumentParser(
                parents=[effect_parser], **parser_args
            )

        executor = XAPIExecutor(
            self, root_parser=root_parser, effect_parser=effect_parser
        )
        return executor.run(argv, namespace)


class XAPIExecutor:
    def __init__(
        self,
        xapi: XAPI,
        root_parser: argparse.ArgumentParser,
        effect_parser: argparse.ArgumentParser,
    ):
        self.xapi = xapi
        self.effect_parser = effect_parser
        self.root_parser = root_parser
        self.parsers: dict[Entrypoint, argparse.ArgumentParser] = {}
        self.accept_kwargs = False
        self.effect_kwargs = False

        self.setup_effects()

        self.setup_entrypoints(
            entrypoints=self.xapi.entrypoints,
            parser=self.root_parser,
            parents=[self.effect_parser],
        )

    def get_argument_args(self, argument: Argument):
        log.debug("retrieving argument args for argument: %r", argument)
        if argument.name is None:
            raise AttributeError(
                "Name is required for argument: %r" % argument
            )

        kwargs = {}

        if argument.help:
            kwargs["help"] = argument.help

        if argument.metavar:
            kwargs["metavar"] = argument.metavar

        if (
            argument.default is not NOT_SPECIFIED
            or (argument.vararg and argument.index is None)
            or argument.annotation is bool
        ):
            # if not argument.required or argument.annotation is bool:
            dashed_name = self.xapi.dashed_name(argument.name)
            if argument.name != dashed_name:
                kwargs["dest"] = argument.name
            if argument.default is not NOT_SPECIFIED:
                kwargs["default"] = argument.default
            args = [f"{'-' * 2}{dashed_name}"]
        else:
            args = [argument.name]

        if argument.aliases:
            args.extend(argument.aliases)

        ctx = _ParserTranslationContext(argument, args, kwargs)

        _translate(ctx)

        return args, kwargs

    def setup_argument(
        self,
        index: int,
        argument: Argument,
        parser: argparse.ArgumentParser,
        doc_info: DocInfo,
    ):
        if argument.vararg and argument.index is None:
            self.accept_kwargs = True

        log.debug("setting up argument for parser: %r", argument)
        args, kwargs = self.get_argument_args(argument)
        kwargs |= doc_info.get_argument_doc_info(index)
        _action = parser.add_argument(*args, **kwargs)
        log.debug(
            "finished setting up parser argument parameter: %r, %r",
            args,
            kwargs,
        )

        return _action

    def setup_arguments(
        self,
        arguments: list[Argument],
        parser: argparse.ArgumentParser,
        doc_info,
    ):
        log.debug("setting up %r arguments", len(arguments))
        args = [
            self.setup_argument(index, argument, parser, doc_info)
            for index, argument in enumerate(arguments)
        ]
        log.debug("finished setting up %r arguments", len(arguments))
        return args

    def setup_effects(self):
        entrypoints = self.xapi.effects

        log.debug("setting up %r effects", len(entrypoints))
        for entrypoint in entrypoints:
            log.debug("setting up effect %r", entrypoint)

            self.setup_arguments(
                entrypoint.arguments,
                self.effect_parser,
                DocInfo(entrypoint.entrypoint),
            )
            if entrypoint.has_kwargs:
                self.effect_kwargs = True

        log.debug("finished setting up %r effects", len(entrypoints))

    def setup_entrypoints(
        self,
        entrypoints: Optional[list[Entrypoint]] = None,
        parser: Optional[argparse.ArgumentParser] = None,
        parents: Optional[argparse.ArgumentParser] = None,
    ):
        entrypoints = entrypoints or self.xapi.entrypoints
        if not parser:
            parser = self.root_parser

        log.debug("setting up %r entrypoints", len(entrypoints))
        sub_parsers = parser.add_subparsers()
        if not parents:
            parents = []

        for entrypoint in entrypoints:
            self.setup_entrypoint(entrypoint, sub_parsers, parents)

        log.debug("finished setting up %r entrypoints", len(entrypoints))

    def setup_entrypoint(
        self,
        entrypoint: Entrypoint,
        parsers: argparse._SubParsersAction,
        parents: list[argparse.ArgumentParser],
    ):
        log.debug("setting up entrypoint: %r", entrypoint)

        if not entrypoint.name:
            raise AttributeError("Bad entrypoint name: %r" % entrypoint)

        kwargs = {
            "help": entrypoint.help,
            "description": entrypoint.description,
            "epilog": entrypoint.epilog,
            "usage": entrypoint.usage,
        }

        if entrypoint.deprecated is not None:
            kwargs["deprecated"] = entrypoint.deprecated

        if parents:
            kwargs["conflict_handler"] = "resolve"
            kwargs["parents"] = parents

        if entrypoint.aliases:
            kwargs["aliases"] = entrypoint.aliases

        doc_info = DocInfo(entrypoint.entrypoint)
        if doc_info:
            kwargs |= doc_info.get_entrypoint_doc_info()

        log.debug(
            "initializing parser with %s with args: %r",
            entrypoint.name,
            kwargs,
        )

        parser: argparse.ArgumentParser = parsers.add_parser(
            entrypoint.name, **kwargs
        )
        parser.set_defaults(__entrypoint__=entrypoint)

        self.parsers[entrypoint] = parser

        if entrypoint.arguments:
            self.setup_arguments(entrypoint.arguments, parser, doc_info)

        if entrypoint.entrypoints:
            # parents.append(parser)
            self.setup_entrypoints(
                entrypoints=entrypoint.entrypoints,
                parser=parser,
                parents=parents,
            )
        log.debug("finished setting up entrypoint: %r", entrypoint)

    def _collect_kwargs(self, raw_kwargs: list[str], default: Any = ""):
        print(raw_kwargs)
        result: dict[str, Any | List[Any]] = {}
        positional = []
        key = None
        for arg in raw_kwargs:
            print(key, arg)
            if arg.startswith("--"):
                if key and result.get(key, None) is None:
                    result[key] = default

                key = arg.lstrip("-")
                # result[key] = default
                continue

            if not key:
                positional.append(arg)
                continue

            cv = result.get(key, None)
            if hasattr(cv, "append"):
                cv.append(arg)
            elif cv is not None:
                result[key] = [cv, arg]
            else:
                result[key] = arg

        if positional:
            raise UserWarning(
                "Found unexpected positional args %r", positional
            )
        return result

    def run(
        self,
        argv: list[str] | None = None,
        namespace: argparse.Namespace | None = None,
    ):
        log.debug("Running xapi executor on args: %r", argv)
        if self.accept_kwargs:
            namespace, raw_kwargs = self.root_parser.parse_known_args(
                argv, namespace
            )
        else:
            namespace = self.root_parser.parse_args(argv, namespace)
            raw_kwargs = {}

        log.debug(
            "processing namespace: %r, unused: %r", namespace, raw_kwargs
        )

        kwargs = self._collect_kwargs(raw_kwargs)
        log.debug("collected extra kwargs: %r", kwargs)
        entrypoint = self._get_namespace_entrypoint(namespace)

        if kwargs and not self.effect_kwargs and not entrypoint.has_kwargs:
            message = f"unrecognized arguments: {kwargs}"
            if self.root_parser.exit_on_error:
                self.root_parser.error(message)
            else:
                raise argparse.ArgumentError(None, message)

        for effect in self.xapi.effects:
            self._call_entrypoint(effect, namespace, kwargs)

        if not entrypoint:
            self._print_and_exit(
                self.root_parser,
                5,
                "Entrypoint not found in command %s" % namespace,
            )

        return self._call_entrypoint(entrypoint, namespace, kwargs)

    def _get_namespace_entrypoint(
        self, namespace: argparse.Namespace
    ) -> Entrypoint:
        return (
            namespace.__entrypoint__
            if hasattr(namespace, "__entrypoint__")
            else None
        )

    def _call_entrypoint(
        self,
        entrypoint: Entrypoint,
        namespace: argparse.Namespace,
        kwargs: Dict[str, str],
    ):
        log.debug("executing entrypoint: %r", entrypoint)

        try:
            return entrypoint.execute(vars(namespace), kwargs, self)
        except AttributeError as e:
            self._print_and_exit(
                self.parsers.get(entrypoint, None), 20, str(e)
            )
        except ConversionError as e:
            self._print_and_exit(
                self.parsers.get(entrypoint, None), 10, str(e)
            )

    def _print_and_exit(
        self, parser: argparse.ArgumentParser, code: int, message: str
    ):
        if not parser:
            parser = self.root_parser

        parser.print_usage()
        parser.exit(code, message)
