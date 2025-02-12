from typing import List, Literal
from xntricweb.xapi.utility import (
    _get_origin_args,
)


def test_origin_args():
    class X[T]:
        pass

    assert _get_origin_args(str) == (str, None)
    assert _get_origin_args(int) == (int, None)
    assert _get_origin_args(list) == (list, None)
    assert _get_origin_args(list[str]) == (list, (str,))
    assert _get_origin_args(tuple[str, int]) == (tuple, (str, int))
    assert _get_origin_args(List[int]) == (list, (int,))
    assert _get_origin_args(X) == (X, None)
    assert _get_origin_args(X[str]) == (X, (str,))
    assert _get_origin_args(Literal["abc", "123"]) == (Literal, ("abc", "123"))
