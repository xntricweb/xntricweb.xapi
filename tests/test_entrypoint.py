import inspect
from typing import Any, Callable

import pytest
from xntricweb.xapi.entrypoint import (
    _get_inspect_arg_details,  # type: ignore
    _get_fn_details,  # type: ignore
)


def no_args():
    pass


def plain_arg(a):  # type: ignore
    pass


def plain_arg_multi(a, b):  # type: ignore
    pass


def plain_arg_defaults(a, b=1, c=2):  # type: ignore
    pass


def plain_var_arg(*j):  # type: ignore
    pass


def plain_arg_var_arg(a, *j):  # type: ignore
    pass


def kw(*, m=4, n=5.0):  # type: ignore
    pass


def adv(a, b=1, c=2, *j, m=4, n=5.0):  # type: ignore
    pass


def adv_annotated(
    a: str, b: float = 1, c: int = 2, *j: int, m: float = 4, n: float = 5.0
):
    pass


cases: list[tuple[Callable[..., Any], list[dict[str, Any]]]] = [
    (no_args, []),
    (plain_arg, [dict(index=0, name="a")]),
    (
        plain_arg_multi,
        [dict(index=0, name="a"), dict(index=1, name="b")],
    ),
    (
        plain_arg_defaults,
        [
            dict(index=0, name="a"),
            dict(index=1, name="b", default=1),
            dict(index=2, name="c", default=2),
        ],
    ),
    (plain_var_arg, [dict(index=0, name="j", vararg=True)]),
    (
        plain_arg_var_arg,
        [dict(index=0, name="a"), dict(index=1, name="j", vararg=True)],
    ),
    (
        kw,
        [
            dict(name="m", default=4),
            dict(name="n", default=5.0),
        ],
    ),
    (
        adv,
        [
            dict(index=0, name="a"),
            dict(index=1, name="b", default=1),
            dict(index=2, name="c", default=2),
            dict(index=3, name="j", vararg=True),
            dict(name="m", default=4),
            dict(name="n", default=5.0),
        ],
    ),
    (
        adv_annotated,
        [
            dict(index=0, name="a", annotation=str),
            dict(index=1, name="b", default=1, annotation=float),
            dict(index=2, name="c", default=2, annotation=int),
            dict(index=3, name="j", vararg=True, annotation=int),
            dict(name="m", default=4, annotation=float),
            dict(name="n", default=5.0, annotation=float),
        ],
    ),
]


@pytest.mark.parametrize(
    argnames="case, expected",
    argvalues=cases,
    ids=[fn[0].__name__ for fn in cases],
)
def test_fn_arg_details(case: Callable[..., Any], expected: list[dict[str, Any]]):
    sig = inspect.signature(case)

    assert _get_inspect_arg_details(list(sig.parameters.values())) == expected


def test_fn_details():
    def testfn():
        """test1"""
        pass

    class testclass:
        """test2"""

        def __call__(self):
            pass

    assert _get_fn_details(testfn) == dict(name="testfn", description="test1")
    assert _get_fn_details(testclass) == dict(name="testclass", description="test2")
