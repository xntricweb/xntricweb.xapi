import inspect
from types import SimpleNamespace

import pytest
from xntricweb.xapi.entrypoint import (
    _get_inspect_arg_details,
    _get_fn_details,
)


class _P:
    POSITIONAL_ONLY = 1
    VAR_KEYWORD = 2
    VAR_POSITIONAL = 3

    empty = object()

    def __init__(self, name, annotation, kind):
        self.name = name
        self.annotation = annotation
        self.kind = kind


def _ns(
    args=[],
    varargs=None,
    varkw=None,
    defaults=None,
    kwonlyargs=[],
    kwonlydefaults=None,
    annotations={},
):
    return SimpleNamespace(**locals())


def _d(**kwargs):
    return kwargs


def no_args():
    pass


def plain_arg(a):
    pass


def plain_arg_multi(a, b):
    pass


def plain_arg_defaults(a, b=1, c=2):
    pass


def plain_var_arg(*j):
    pass


def plain_arg_var_arg(a, *j):
    pass


def kw(*, m=4, n=5.0):
    pass


def adv(a, b=1, c=2, *j, m=4, n=5.0):
    pass


def adv_annotated(
    a: str, b: float = 1, c: int = 2, *j: int, m: float = 4, n: float = 5.0
):
    pass


cases = [
    (no_args, []),
    (plain_arg, [_d(index=0, name="a")]),
    (
        plain_arg_multi,
        [_d(index=0, name="a"), _d(index=1, name="b")],
    ),
    (
        plain_arg_defaults,
        [
            _d(index=0, name="a"),
            _d(index=1, name="b", default=1, annotation=int),
            _d(index=2, name="c", default=2, annotation=int),
        ],
    ),
    (plain_var_arg, [_d(index=0, name="j", vararg=True)]),
    (
        plain_arg_var_arg,
        [_d(index=0, name="a"), _d(index=1, name="j", vararg=True)],
    ),
    (
        kw,
        [
            _d(name="m", default=4, annotation=int),
            _d(name="n", default=5.0, annotation=float),
        ],
    ),
    (
        adv,
        [
            _d(index=0, name="a"),
            _d(index=1, name="b", default=1, annotation=int),
            _d(index=2, name="c", default=2, annotation=int),
            _d(index=3, name="j", vararg=True),
            _d(name="m", default=4, annotation=int),
            _d(name="n", default=5.0, annotation=float),
        ],
    ),
    (
        adv_annotated,
        [
            _d(index=0, name="a", annotation=str),
            _d(index=1, name="b", default=1, annotation=float),
            _d(index=2, name="c", default=2, annotation=int),
            _d(index=3, name="j", vararg=True, annotation=int),
            _d(name="m", default=4, annotation=float),
            _d(name="n", default=5.0, annotation=float),
        ],
    ),
]


@pytest.mark.parametrize(
    argnames="case, expected",
    argvalues=cases,
    ids=[fn[0].__name__ for fn in cases],
)
def test_fn_arg_details(case, expected):
    sig = inspect.signature(case)

    assert _get_inspect_arg_details(sig.parameters.values()) == expected


def test_fn_details():
    def testfn():
        """test1"""
        pass

    class testclass:
        """test2"""

        def __call__(self):
            pass

    assert _get_fn_details(testfn) == _d(name="testfn", description="test1")
    assert _get_fn_details(testclass) == _d(
        name="testclass", description="test2"
    )
