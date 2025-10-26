from typing import Any, Literal, cast

import pytest
from xntricweb.xapi.xapi import XAPIExecutor, XAPI
from xntricweb.xapi.arguments import Argument
from types import SimpleNamespace
import unittest.mock as mocks

import argparse

# from argparse import ArgumentParser

mock_EffectParser = mocks.MagicMock()
mock_ArgumentParser = mocks.MagicMock()
mock_ArgumentParser.prefix_chars = ["-"]

mocks.patch("argparse.ArgumentParser", mock_ArgumentParser)


mock_parser = SimpleNamespace(prefix_chars="-")

type TestParams = Argument
type ExpectedParams = tuple[list[Any], dict[str, Any]]
type TestCase = tuple[TestParams, ExpectedParams]

_executor = XAPIExecutor(XAPI(), mock_ArgumentParser, mock_EffectParser)


def gen(arg: Argument) -> tuple[list[str], dict[str, Any]]:
    # args = []
    # kwargs = {}
    return _executor.get_argument_args(arg)
    # return _XAPIExecutor.get_argument_args(arg, p)
    # return args, kwargs


def _dd(default: Any = None, **kwargs: Any):
    kwargs["default"] = default
    return kwargs


def test_positional():
    cases: list[TestCase] = [
        (Argument("named"), (["named"], {})),
        (
            Argument("name_underscored"),
            (["name_underscored"], dict()),
        ),
        # (
        #     Argument("name_default", default=1),
        #     (["--name-default"], _d(default=1, dest="name_default")),
        # ),
        (
            Argument("annotated", annotation=int),
            (["annotated"], dict()),
        ),
        (
            Argument("help", help="help text"),
            (["help"], dict(help="help text")),
        ),
        (
            Argument("aliased", aliases=["a"]),
            (["aliased", "a"], {}),
        ),
        (
            Argument("metavar", metavar="metavar text"),
            (["metavar"], dict(metavar="metavar text")),
        ),
        (
            Argument("varargs", index=0, vararg=True),
            (["varargs"], dict(nargs="*")),
        ),
        (
            Argument(
                "all_together",
                annotation=int,
                index=0,
                vararg=True,
                aliases=["at"],
                help="all together help",
                metavar="all together metavar",
            ),
            (
                ["all_together", "at"],
                dict(
                    help="all together help",
                    metavar="all together metavar",
                    nargs="*",
                ),
            ),
        ),
    ]

    for case, expected in cases:
        actual = gen(case)
        print(actual)
        assert actual == expected


@pytest.mark.parametrize(
    argnames="case, expected",
    argvalues=[
        (Argument("named", default=None), (["--named"], _dd())),
        (
            Argument("name_underscored", default=None),
            (
                ["--name-underscored"],
                _dd(dest="name_underscored"),
            ),
        ),
        (
            Argument("annotated", annotation=int, default=1),
            (["--annotated"], _dd(1)),
        ),
        (
            Argument("help", help="help text", default=None),
            (["--help"], _dd(help="help text")),
        ),
        (
            Argument("aliased", aliases=["-a"], default=None),
            (["--aliased", "-a"], _dd()),
        ),
        (
            Argument("metavar", metavar="metavar text", default=None),
            (["--metavar"], _dd(metavar="metavar text")),
        ),
        (
            Argument("varargs", vararg=True),
            (
                ["--varargs"],
                dict(action="store_const", const="KWARG"),
            ),
        ),
        (
            Argument(
                "all_together",
                annotation=int,
                vararg=True,
                aliases=["at"],
                help="all together help",
                metavar="all together metavar",
            ),
            (
                ["--all-together", "at"],
                dict(
                    help="all together help",
                    metavar="all together metavar",
                    dest="all_together",
                    action="store_const",
                    const="KWARG",
                ),
            ),
        ),
    ],
)
def test_optional(case: Argument, expected: tuple[list[str], dict[str, Any]]):
    actual = gen(case)
    assert actual == expected


def test_special_annotations():
    cases = [
        (
            Argument("bool", annotation=bool),
            (["--bool"], dict(default=False, action="store_true")),
        ),
        # (
        #     Argument("const", annotation=Literal[5]),
        #     (["const"], _d(action="store_const", const=5)),
        # ),
        (
            Argument("choice", annotation=Literal["run", "walk"]),
            (["choice"], dict(choices=["run", "walk"])),
        ),
        (
            Argument("list", annotation=list[int]),
            (["list"], dict(nargs="*")),
        ),
        (
            Argument("tuple", annotation=tuple[int, float, str]),
            (["tuple"], dict(nargs=3)),
        ),
    ]

    for case, expected in cases:
        actual = gen(case)
        assert actual == expected


test_cases_positional_setup_argument: list[
    tuple[Argument, list[str], tuple[list[Any], dict[str, Any]]]
] = [
    (
        Argument("int", index=0, annotation=int),
        ["1"],
        ([1], {}),
    ),
    (
        Argument("float", index=0, annotation=float),
        ["1.933"],
        ([1.933], {}),
    ),
    (
        Argument("string", index=0, annotation=str),
        ["2"],
        (["2"], {}),
    ),
    (
        Argument("vararg", index=0, vararg=True),
        list("abcdef".split()),
        ([*("abcdef".split())], {}),
    ),
    (
        Argument("vararg_int", index=0, annotation=int, vararg=True),
        list(map(str, range(10))),
        ([*range(10)], {}),
    ),
    (
        Argument("list_strings", index=0, annotation=list[str]),
        list("abcdef".split()),
        (["abcdef".split()], {}),
    ),
    (
        Argument("list_ints", index=0, annotation=list[int]),
        list(map(str, range(10))),
        ([list(range(10))], {}),
    ),
    (
        Argument("list_unspecified", index=0, annotation=list),
        list(map(str, range(10))),
        ([list(map(str, range(10)))], {}),
    ),
    (
        Argument("list_empty", index=0, annotation=list[str]),
        [],
        ([[]], {}),
    ),
    (
        Argument("tuple", index=0, annotation=tuple[str, int]),
        ["1", "2"],
        ([("1", 2)], {}),
    ),
    (
        Argument("tuple_unspecified", index=0, annotation=tuple),
        ["1", "2"],
        ([("1", "2")], {}),
    ),
    (
        Argument("tuple_unspecified_empty", index=0, annotation=tuple),
        [],
        ([tuple()], {}),
    ),
]


@pytest.mark.parametrize(
    "argument, parse_args, expected",
    test_cases_positional_setup_argument,
    ids=[arg[0].name for arg in test_cases_positional_setup_argument],
)
def test_positional_setup_argument(
    argument: Argument,
    parse_args: list[str],
    expected: tuple[list[Any], dict[str, Any]],
):
    parser = argparse.ArgumentParser(exit_on_error=False)
    _executor.setup_argument(
        0,
        argument,
        parser,
        mocks.MagicMock(),
        # SimpleNamespace(get_argument_doc_info=lambda _: {}),
    )
    result = vars(parser.parse_args(parse_args))
    args, kwargs = cast(tuple[list[Any], dict[str, Any]], ([], {}))
    argument.generate_call_arg(result.get(argument.name), args, kwargs)
    assert (args, kwargs) == expected


test_cases_optional_setup_argument: list[
    tuple[Argument, list[str], tuple[list[Any], dict[str, Any]]]
] = [
    (
        Argument("int", default=3, annotation=int),
        ["--int", "1"],
        ([], dict(int=1)),
    ),
    (
        Argument("int_notprovided", default=3, annotation=int),
        [],
        ([], dict()),
    ),
    (
        Argument("float", default=3.4, annotation=float),
        ["--float", "3.6"],
        ([], dict(float=3.6)),
    ),
    (
        Argument("float_notprovided", default=3.4, annotation=float),
        [],
        ([], dict()),
    ),
    (
        Argument("string", default="54", annotation=str),
        ["--string", "2"],
        ([], dict(string="2")),
    ),
    (
        Argument("list_strings", default=3, annotation=list[str]),
        ["--list-strings", *"abcdef".split()],
        ([], dict(list_strings="abcdef".split())),
    ),
    (
        Argument("list_ints", default=[], annotation=list[int]),
        ["--list-ints", *list(map(str, range(10)))],
        ([], dict(list_ints=list(range(10)))),
    ),
    (
        Argument("list_unspecified", default=3, annotation=list),
        ["--list-unspecified", *list(map(str, range(10)))],
        ([], dict(list_unspecified=list(map(str, range(10))))),
    ),
    (
        Argument(
            "list_not_provided",
            default=["3", "4", "5"],
            annotation=list[str],
        ),
        [],
        ([], dict()),
    ),
    (
        Argument("list_empty", default=["3", "4", "5"], annotation=list[str]),
        ["--list-empty"],
        ([], dict(list_empty=[])),
    ),
    (
        Argument("tuple", default=(3, 4), annotation=tuple[str, int]),
        ["--tuple", "1", "2"],
        ([], dict(tuple=("1", 2))),
    ),
    (
        Argument("tuple_unspecified", default=("3", "4"), annotation=tuple),
        ["--tuple-unspecified", "1", "2"],
        ([], dict(tuple_unspecified=("1", "2"))),
    ),
    (
        Argument(
            "tuple_unspecified_not_provided",
            default=("3", "4"),
            annotation=tuple,
        ),
        [],
        ([], dict()),
    ),
    (
        Argument("tuple_unspecified_empty", default=(3, 4), annotation=tuple),
        [],
        ([], dict()),
    ),
]


@pytest.mark.parametrize(
    "argument, parse_args, expected",
    test_cases_optional_setup_argument,
    ids=[arg[0].name for arg in test_cases_optional_setup_argument],
)
def test_optional_setup_argument(
    argument: Argument,
    parse_args: list[str],
    expected: tuple[list[Any], dict[str, Any]],
):
    print("processing %r" % argument)
    parser = argparse.ArgumentParser(exit_on_error=False)
    _executor.setup_argument(
        0,
        argument,
        parser,
        mocks.MagicMock(),
    )
    result = vars(parser.parse_args(parse_args))
    args, kwargs = cast(tuple[list[Any], dict[str, Any]], ([], {}))
    argument.generate_call_arg(result.get(argument.name), args, kwargs)
    print("processed %r" % argument)
    assert (args, kwargs) == expected, f"{argument.name} failed"
