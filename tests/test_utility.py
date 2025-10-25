from typing import List, Literal
from xntricweb.xapi.utility import (
    get_origin_args,
)


def test_origin_args():
    class X[T]:
        pass

    assert get_origin_args(str) == (str, ())
    assert get_origin_args(int) == (int, ())
    assert get_origin_args(list) == (list, ())
    assert get_origin_args(list[str]) == (list, (str,))
    assert get_origin_args(tuple[str, int]) == (tuple, (str, int))
    assert get_origin_args(List[int]) == (list, (int,))
    assert get_origin_args(X) == (X, ())
    assert get_origin_args(X[str]) == (X, (str,))
    assert get_origin_args(Literal["abc", "123"]) == (Literal, ("abc", "123"))
