import argparse
from enum import Enum
from typing import Callable, Literal, Optional, Type

from xntricweb.xapi.utility import coalesce

from .arguments import Argument, ConversionError
from .entrypoint import Entrypoint

from .const import log
from .utility import _get_origin_args
from .xapi_docstring_parser import DocInfo


# entrypoint_parsers: dict[Entrypoint, argparse.ArgumentParser] = {}


def default_translator(arg, origin, _, args, kwargs):
    pass


def literal_translator(arg, origin, literals, args, kwargs):
    if len(literals) > 1:
        kwargs["choices"] = list(literals)
    elif len(literals) == 1:
        raise AttributeError("single Literal option not supported")
    #     raise TypeError("Literal with single value is not supported")
    #     kwargs["const"] = literals[0]
    #     kwargs["action"] = "store_const"
    else:
        raise TypeError("Cannot translate empty literal expression.")


def bool_translator(arg, origin, _, args, kwargs):
    state = coalesce(arg.default, True)
    kwargs["action"] = f"store_{str(state).lower()}"


def list_translator(arg, origin, _, args, kwargs):
    kwargs["nargs"] = "*"


def tuple_translator(arg, origin, terms, args, kwargs):
    if terms:
        kwargs["nargs"] = len(terms)
    else:
        kwargs["nargs"] = "*"


def enum_translator(arg, origin, terms, args, kwargs):
    kwargs["choices"] = [k for k in vars(origin) if not k[0] == "_"]


class XAPI:

    def __init__(self):
        self.effects: list[Entrypoint] = []
        self.entrypoints: list[Entrypoint] = []
        self.translators = {
            bool: bool_translator,
            list: list_translator,
            tuple: tuple_translator,
            Literal: literal_translator,
            Enum: enum_translator,
        }

    def dashed_name(self, name: str):
        return name.replace("_", "-")

    def get_translator(self, origin):

        translator = self.translators.get(origin, None)
        if not translator:
            if not hasattr(origin, "__bases__"):
                origin = origin.__class__

            for base in reversed(origin.__bases__):
                translator = self.translators.get(base)
                if translator:
                    break

        return translator or default_translator

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
        def wrap(fn: Callable | Entrypoint = None):
            if isinstance(fn, Entrypoint):
                _entrypoint = fn

            elif type(fn) is type and issubclass(fn, Entrypoint):
                log.debug("setting up decorated class entrypoint")
                _entrypoint = fn(**kwargs)

            elif isinstance(fn, Callable):
                _entrypoint = Entrypoint.from_function(fn, **kwargs)
            else:
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
        root_parser: argparse.ArgumentParser | None = None,
        **parser_args,
    ):
        if not root_parser:
            root_parser = argparse.ArgumentParser(**parser_args)

        executor = XAPIExecutor(self, root_parser=root_parser)
        return executor.run(argv, namespace)


class XAPIExecutor:
    def __init__(self, xapi: XAPI, root_parser: argparse.ArgumentParser):
        self.xapi = xapi
        self.effect_parser = argparse.ArgumentParser(add_help=False)
        self.parsers: dict[Entrypoint, argparse.ArgumentParser] = {}

        self.setup_effects()
        self.root_parser = argparse.ArgumentParser(
            parents=[self.effect_parser]
        )

        self.setup_entrypoints(
            entrypoints=self.xapi.entrypoints,
            parser=self.root_parser,
            parents=[self.effect_parser],
        )

    def get_argument_args(self, argument: Argument):
        if argument.name is None:
            raise AttributeError(
                "Name is required for argument: %r" % argument
            )

        kwargs = {}

        if argument.help:
            kwargs["help"] = argument.help

        if argument.metavar:
            kwargs["metavar"] = argument.metavar

        if not argument.required:
            dashed_name = self.xapi.dashed_name(argument.name)
            if argument.name != dashed_name:
                kwargs["dest"] = argument.name
            kwargs["default"] = argument.default
            args = [f"{'-' * 2}{dashed_name}"]
        else:
            args = [argument.name]

        if argument.aliases:
            args.extend(argument.aliases)

        if argument.vararg:
            origin = list
            origin_args = (argument.annotation,)
        else:
            origin, origin_args = _get_origin_args(argument.annotation)

        translator = self.xapi.get_translator(origin)

        log.debug(f"using {translator.__name__} for argument translation")
        translator(argument, origin, origin_args, args, kwargs)

        return args, kwargs

    def setup_argument(
        self,
        index: int,
        argument: Argument,
        parser: argparse.ArgumentParser,
        doc_info: DocInfo,
    ):
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

    def run(
        self,
        argv: list[str] | None = None,
        namespace: argparse.Namespace | None = None,
    ):
        namespace = self.root_parser.parse_args(argv, namespace)

        for effect in self.xapi.effects:
            self._call_entrypoint(effect, namespace)

        entrypoint = self._get_namespace_entrypoint(namespace)
        if not entrypoint:
            self._print_and_exit(
                self.root_parser,
                5,
                "Entrypoint not found in command %s" % namespace,
            )

        return self._call_entrypoint(entrypoint, namespace)

    def _get_namespace_entrypoint(
        self, namespace: argparse.Namespace
    ) -> Entrypoint:
        return (
            namespace.__entrypoint__
            if hasattr(namespace, "__entrypoint__")
            else None
        )

    def _call_entrypoint(
        self, entrypoint: Entrypoint, namespace: argparse.Namespace
    ):
        log.debug("executing entrypoint: %r", entrypoint)
        try:
            return entrypoint.execute(vars(namespace), self)
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
