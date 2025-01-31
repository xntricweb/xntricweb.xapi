import argparse
from typing import Callable, Optional, _LiteralGenericAlias

from .arguments import Argument
from .entrypoint import root_effects, root_entrypoints, Entrypoint

from .const import log


entrypoint_parsers: dict[Entrypoint, argparse.ArgumentParser] = {}


class _EffectAction(argparse.Action):
    def __init__(
        self,
        option_strings,
        dest,
        nargs=None,
        const=None,
        default=None,
        type=None,
        choices=None,
        required=False,
        help=None,
        metavar=None,
        deprecated=False,
    ):
        if not isinstance(const, Callable):
            raise "const must be callable when using the effect action."

        super().__init__(
            option_strings,
            dest,
            nargs,
            const,
            default,
            type,
            choices,
            required,
            help,
            metavar,
            deprecated,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        _values = self.const(values)
        setattr(namespace, self.dest, _values)


def get_argument_args(argument: Argument, parser: argparse.ArgumentParser):
    if argument.name is None:
        raise AttributeError("Name is required for argument: %r" % argument)

    kwargs = {
        "help": argument.help,
        # "metavar": argument.metavar,
    }

    if not argument.vararg and not argument.required:
        kwargs["default"] = argument.default
        args = [f"{parser.prefix_chars[0] * 2}{argument.name}"]
    else:
        args = [argument.name]

    if argument.aliases:
        args.extend(argument.aliases)

    if argument.vararg and argument.index is not None:
        kwargs["nargs"] = "*"

    elif argument.annotation == bool and argument.default is not None:
        kwargs["action"] = f"store_{str(argument.default).lower()}"

    elif isinstance(argument.annotation, _LiteralGenericAlias):
        items = argument.annotation.__args__
        if len(items) > 1:
            kwargs["choices"] = items
        else:
            kwargs["const"] = items[0]
            kwargs["action"] = "store_const"

    elif isinstance(argument.annotation, Callable):
        kwargs["type"] = argument.annotation

    return args, kwargs


def setup_argument(argument: Argument, parser: argparse.ArgumentParser):
    log.debug("applying argument %r to parser %r", argument, parser)
    args, kwargs = get_argument_args(argument, parser)
    _action = parser.add_argument(*args, **kwargs)
    log.debug("applied parser argument parameters: %r, %r", args, kwargs)

    return _action


def setup_arguments(
    arguments: list[Argument], parser: argparse.ArgumentParser
):
    return [setup_argument(argument, parser) for argument in arguments]


def setup_entrypoint(
    entrypoint: Entrypoint,
    parsers: argparse._SubParsersAction,
    parents: list[argparse.ArgumentParser],
):

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
        kwargs["parents"] = parents

    if entrypoint.aliases:
        kwargs["aliases"] = entrypoint.aliases

    parser: argparse.ArgumentParser = parsers.add_parser(
        entrypoint.name, **kwargs
    )
    parser.set_defaults(__entrypoint__=entrypoint)

    entrypoint_parsers[entrypoint.name] = parser

    if entrypoint.arguments:
        setup_arguments(entrypoint.arguments, parser)

    if entrypoint.entrypoints:
        parents.append(parser)
        setup_entrypoints(
            entrypoints=entrypoint.entrypoints, parser=parser, parents=parents
        )


def setup_effects(
    entrypoints: list[Entrypoint],
    parser: argparse.ArgumentParser,
):
    for entrypoint in entrypoints:
        for argument in entrypoint.arguments:
            action = setup_argument(argument, parser)


def setup_entrypoints(
    entrypoints: list[Entrypoint],
    parser: argparse.ArgumentParser,
    parents: Optional[argparse.ArgumentParser] = None,
):
    sub_parsers = parser.add_subparsers()
    for entrypoint in entrypoints:
        setup_entrypoint(entrypoint, sub_parsers, parents)


def _call_entrypoint(namespace):

    entrypoint: Entrypoint = namespace.__entrypoint__

    log.debug("executing entrypoint: %r", entrypoint)

    return entrypoint.execute(vars(namespace))


def setup(parser: argparse.ArgumentParser = None):
    if not parser:
        parser = argparse.ArgumentParser()

    parser.register("action", "effect", _EffectAction)

    setup_entrypoints(root_entrypoints, parser)
    setup_effects(root_effects, parser)

    return parser


def run(argv: list[str] = None, parser: argparse.ArgumentParser = None):
    if not parser:
        parser = setup(parser)

    namespace = parser.parse_args(argv)
    if not hasattr(namespace, "__entrypoint__"):
        parser.print_usage()
        parser.exit(1, "Entrypoint not found in command %s" % namespace)

    # process effects
    for effect_entry in root_effects:
        effect_entry.execute(vars(namespace))

    return _call_entrypoint(namespace)
