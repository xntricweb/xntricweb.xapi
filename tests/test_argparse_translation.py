from typing import Literal

import pytest
from xntricweb.xapi.xapi import XAPIExecutor, XAPI
from xntricweb.xapi.arguments import Argument
from types import SimpleNamespace
import unittest.mock as mocks

import argparse

# from argparse import ArgumentParser

mock_ArgumentParser = mocks.MagicMock()
mock_ArgumentParser.prefix_chars = ["-"]

mocks.patch("argparse.ArgumentParser", mock_ArgumentParser)


mock_parser = SimpleNamespace(prefix_chars="-")


_executor = XAPIExecutor(XAPI(), mock_ArgumentParser)


def gen(arg):
    # args = []
    # kwargs = {}
    return _executor.get_argument_args(arg)
    # return _XAPIExecutor.get_argument_args(arg, p)
    # return args, kwargs


def _d(**kwargs):
    return kwargs


def _dd(default=None, **kwargs):
    kwargs["default"] = default
    return kwargs


def _p(key):
    return "--" + key


def test_positional():
    cases = [
        (Argument("named"), (["named"], {})),
        (
            Argument("name_underscored"),
            (["name_underscored"], _d()),
        ),
        # (
        #     Argument("name_default", default=1),
        #     (["--name-default"], _d(default=1, dest="name_default")),
        # ),
        (
            Argument("annotated", annotation=int),
            (["annotated"], _d()),
        ),
        (
            Argument("help", help="help text"),
            (["help"], _d(help="help text")),
        ),
        (
            Argument("aliased", aliases=["a"]),
            (["aliased", "a"], {}),
        ),
        (
            Argument("metavar", metavar="metavar text"),
            (["metavar"], _d(metavar="metavar text")),
        ),
        (
            Argument("varargs", vararg=True),
            (["varargs"], _d(nargs="*")),
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
                _d(
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


def test_optional():
    cases = [
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
            Argument("varargs", vararg=True, default=None),
            (["--varargs"], _dd(nargs="*")),
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
                default=None,
            ),
            (
                ["--all-together", "at"],
                _dd(
                    help="all together help",
                    metavar="all together metavar",
                    dest="all_together",
                    nargs="*",
                ),
            ),
        ),
    ]

    for case, expected in cases:
        actual = gen(case)
        print(actual)
        assert actual == expected


def test_special_annotations():
    cases = [
        (
            Argument("bool", annotation=bool),
            (["bool"], _d(action="store_true")),
        ),
        # (
        #     Argument("const", annotation=Literal[5]),
        #     (["const"], _d(action="store_const", const=5)),
        # ),
        (
            Argument("choice", annotation=Literal["run", "walk"]),
            (["choice"], _d(choices=["run", "walk"])),
        ),
        (
            Argument("list", annotation=list[int]),
            (["list"], _d(nargs="*")),
        ),
        (
            Argument("tuple", annotation=tuple[int, float, str]),
            (["tuple"], _d(nargs=3)),
        ),
    ]

    for case, expected in cases:
        actual = gen(case)
        assert actual == expected


test_cases_positional_setup_argument = [
    (
        Argument("int", annotation=int),
        ["1"],
        ([1], {}),
    ),
    (
        Argument("float", annotation=float),
        ["1.933"],
        ([1.933], {}),
    ),
    (
        Argument("string", annotation=str),
        ["2"],
        (["2"], {}),
    ),
    (
        Argument("vararg", vararg=True),
        "abcdef".split(),
        ([*("abcdef".split())], {}),
    ),
    (
        Argument("vararg_int", annotation=int, vararg=True),
        list(map(str, range(10))),
        ([*range(10)], {}),
    ),
    (
        Argument("list_strings", annotation=list[str]),
        "abcdef".split(),
        (["abcdef".split()], {}),
    ),
    (
        Argument("list_ints", annotation=list[int]),
        list(map(str, range(10))),
        ([list(range(10))], {}),
    ),
    (
        Argument("list_unspecified", annotation=list),
        list(map(str, range(10))),
        ([list(map(str, range(10)))], {}),
    ),
    (
        Argument("list_empty", annotation=list[str]),
        [],
        ([[]], {}),
    ),
    (
        Argument("tuple", annotation=tuple[str, int]),
        ["1", "2"],
        ([("1", 2)], {}),
    ),
    (
        Argument("tuple_unspecified", annotation=tuple),
        ["1", "2"],
        ([("1", "2")], {}),
    ),
    (
        Argument("tuple_unspecified_empty", annotation=tuple),
        [],
        ([tuple()], {}),
    ),
]


@pytest.mark.parametrize(
    "argument, parse_args, expected",
    test_cases_positional_setup_argument,
    ids=[arg[0].name for arg in test_cases_positional_setup_argument],
)
def test_positional_setup_argument(argument, parse_args, expected):
    parser = argparse.ArgumentParser(exit_on_error=False)
    _executor.setup_argument(
        0,
        argument,
        parser,
        SimpleNamespace(get_argument_doc_info=lambda _: {}),
    )
    result = vars(parser.parse_args(parse_args))
    args, kwargs = ([], {})
    argument.generate_call_arg(result.get(argument.name), args, kwargs)
    assert (args, kwargs) == expected


test_cases_optional_setup_argument = [
    (
        Argument("int", default=3, annotation=int),
        ["--int", "1"],
        ([], _d(int=1)),
    ),
    (
        Argument("int_notprovided", default=3, annotation=int),
        [],
        ([], _d()),
    ),
    (
        Argument("float", default=3.4, annotation=float),
        ["--float", "3.6"],
        ([], _d(float=3.6)),
    ),
    (
        Argument("float_notprovided", default=3.4, annotation=float),
        [],
        ([], _d()),
    ),
    (
        Argument("string", default="54", annotation=str),
        ["--string", "2"],
        ([], _d(string="2")),
    ),
    (
        Argument("list_strings", default=3, annotation=list[str]),
        ["--list-strings", *"abcdef".split()],
        ([], _d(list_strings="abcdef".split())),
    ),
    (
        Argument("list_ints", default=3, annotation=list[int]),
        ["--list-ints", *list(map(str, range(10)))],
        ([], _d(list_ints=list(range(10)))),
    ),
    (
        Argument("list_unspecified", default=3, annotation=list),
        ["--list-unspecified", *list(map(str, range(10)))],
        ([], _d(list_unspecified=list(map(str, range(10))))),
    ),
    (
        Argument(
            "list_not_provided",
            default=["3", "4", "5"],
            annotation=list[str],
        ),
        [],
        ([], _d()),
    ),
    (
        Argument("list_empty", default=["3", "4", "5"], annotation=list[str]),
        ["--list-empty"],
        ([], _d(list_empty=[])),
    ),
    (
        Argument("tuple", default=(3, 4), annotation=tuple[str, int]),
        ["--tuple", "1", "2"],
        ([], _d(tuple=("1", 2))),
    ),
    (
        Argument("tuple_unspecified", default=("3", "4"), annotation=tuple),
        ["--tuple-unspecified", "1", "2"],
        ([], _d(tuple_unspecified=("1", "2"))),
    ),
    (
        Argument(
            "tuple_unspecified_not_provided",
            default=("3", "4"),
            annotation=tuple,
        ),
        [],
        ([], _d()),
    ),
    (
        Argument("tuple_unspecified_empty", default=(3, 4), annotation=tuple),
        [],
        ([], _d()),
    ),
]


@pytest.mark.parametrize(
    "argument, parse_args, expected",
    test_cases_optional_setup_argument,
    ids=[arg[0].name for arg in test_cases_optional_setup_argument],
)
def test_optional_setup_argument(argument, parse_args, expected):
    print("processing %r" % argument)
    parser = argparse.ArgumentParser(exit_on_error=False)
    _executor.setup_argument(
        0,
        argument,
        parser,
        SimpleNamespace(get_argument_doc_info=lambda _: {}),
    )
    result = vars(parser.parse_args(parse_args))
    args, kwargs = ([], {})
    argument.generate_call_arg(result.get(argument.name), args, kwargs)
    print("processed %r" % argument)
    assert (args, kwargs) == expected, f"{argument.name} failed"
