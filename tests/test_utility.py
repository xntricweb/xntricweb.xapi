from typing import List, Literal
from xntricweb.xapi.utility import get_origin_args, is_any, coalesce


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


def test_is_any() -> None:
    assert is_any(type(""), [str])
    assert is_any(True, [True])
    assert is_any(False, [False])
    assert not is_any(None, [False])
    assert not is_any(False, [None])
    assert not is_any(True, [False, None])
    assert is_any(True, [False, True])


def test_coalesce() -> None:
    like_none = object()

    assert coalesce(1, None) == 1
    assert coalesce(None, None, 1) == 1
    assert coalesce(False, False, 1) == 1
    assert coalesce("", "", 2) == 2
    assert coalesce(True, False, 1) is True
    assert coalesce("", False, None) is None
    assert coalesce(None, like_none, None, 4) is like_none
    assert (
        coalesce(None, like_none, is_not=[like_none], check_falsey=False)
        is None
    )
    assert coalesce(None, like_none, False, 4, also_is_not=[like_none]) == 4
    assert coalesce(None, like_none, None, 4, is_not=[None, like_none]) == 4
    assert coalesce("", like_none, None, 4, is_not=[None, like_none]) == 4
    assert "" == coalesce(None, "", None, is_not=[None], check_falsey=False)
    assert False is coalesce(
        None, False, None, is_not=[None], check_falsey=False
    )
