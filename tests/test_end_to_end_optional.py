import argparse
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal, Optional, cast

import pytest

from xntricweb.xapi.xapi import XAPI


def track_calls(fn: Callable[..., Any]):
    setattr(fn, "_calls", getattr(fn, "_calls", 0) + 1)


def assert_called(fn: Callable[..., Any], count: int = 1):
    assert getattr(fn, "_calls", 0) == count


def test_no_args():
    xapi = XAPI()

    @xapi.entrypoint
    def case():
        track_calls(case)
        return 32423

    assert xapi.run(["case"]) == 32423
    assert_called(case, 1)


def test_optional_string():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[str] = None):
        track_calls(case)
        return value

    assert xapi.run(list("case --value abc".split(" "))) == "abc"
    assert xapi.run(list("case".split(" "))) is None
    assert_called(case, 2)


def test_basic_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value="5"):  # type: ignore Testing case when parameter is not annotated
        track_calls(case)
        return value

    assert xapi.run(["case", "--value", "abc"], exit_on_error=False) == "abc"
    assert xapi.run(["case"], exit_on_error=False) == "5"
    assert_called(case, 2)


def test_datetime():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[datetime] = None):
        track_calls(case)
        return value and value.isoformat()

    assert (
        xapi.run(["case", "--value", "2025-02-16T22:00"], exit_on_error=False)
        == "2025-02-16T22:00:00"
    )
    assert xapi.run(["case"], exit_on_error=False) is None
    assert_called(case, 2)


def test_annotated_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: int = 4):
        track_calls(case)
        return value

    assert xapi.run(["case", "--value", "549"], exit_on_error=False) == 549
    assert xapi.run(["case"], exit_on_error=False) == 4
    assert_called(case, 2)


def test_list_optional():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[list[Any]] = None):
        track_calls(case)
        return "".join(value or [])

    assert (
        xapi.run(list("case --value 13 14 52".split(" ")), exit_on_error=False)
        == "131452"
    )
    assert xapi.run(["case"], exit_on_error=False) == ""
    assert_called(case, 2)


def test_list_union():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: list[Any] | None = None):
        track_calls(case)
        return "".join(value or [])

    assert (
        xapi.run(["case", "--value", "13", "14", "52"], exit_on_error=False) == "131452"
    )
    assert xapi.run(["case"], exit_on_error=False) == ""
    assert_called(case, 2)


def test_list_int():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[list[int]] = None):
        track_calls(case)
        return sum(value or [])

    assert (
        xapi.run(
            ["case", "--value", "13", "14", "52"],
            exit_on_error=False,
        )
        == 79
    )
    assert xapi.run(["case"], exit_on_error=False) == 0
    assert_called(case, 2)


def test_list_empty():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[list[int]] = None):
        track_calls(case)
        return sum(value or [])

    assert xapi.run(["case", "--value"], exit_on_error=False) == 0
    assert xapi.run(["case"], exit_on_error=False) == 0
    assert_called(case, 2)


def test_tuple():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[tuple[Any, ...]] = None):
        track_calls(case)
        return f"{value or tuple()}"

    assert (
        xapi.run(["case", "--value", "13", "14", "52"], exit_on_error=False)
        == "('13', '14', '52')"
    )

    assert xapi.run(["case"], exit_on_error=False) == "()"
    assert_called(case, 2)


def test_tuple_typed():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[tuple[str, int]] = None):
        track_calls(case)
        if not value:
            return
        return f"{':'.join([str(v) for v in value] or [])}"

    assert (
        xapi.run(list("case --value abc 123".split(" ")), exit_on_error=False)
        == "abc:123"
    )
    assert xapi.run(["case"], exit_on_error=False) is None
    assert_called(case, 2)


def test_literal_single():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Literal["min"] | None = None):
        track_calls(case)
        return value

    assert xapi.run(list("case --value min".split(" ")), exit_on_error=False) == "min"
    assert_called(case, 1)


def test_literal_multi_min():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[Literal["min", "max"]] = "max"):
        track_calls(case)
        return value

    assert xapi.run(list("case --value min".split(" ")), exit_on_error=False) == "min"

    # assert xapi.run(list("case".split(" ")), exit_on_error=False) == "max"
    assert_called(case, 1)


def test_literal_multi_min_optional():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[Literal["min", "max"]] = None):
        track_calls(case)
        return value

    assert xapi.run(list("case --value min".split(" ")), exit_on_error=False) == "min"

    assert xapi.run(list("case".split(" ")), exit_on_error=False) is None
    assert_called(case, 2)


def test_boolean_default_false():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[bool] = False):
        track_calls(case)
        return value

    with pytest.raises(SystemExit):
        assert xapi.run(list("case --value true".split(" "))) is True

    assert xapi.run(list("case --value".split(" ")), exit_on_error=False) is True

    assert xapi.run(list("case".split(" ")), exit_on_error=False) is False
    assert_called(case, 2)


def test_boolean_default_true():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[bool] = True):
        track_calls(case)
        return value

    with pytest.raises(argparse.ArgumentError):
        assert (
            xapi.run(list("case --value true".split(" ")), exit_on_error=False) is True
        )

    assert xapi.run(list("case --value".split(" ")), exit_on_error=False) is False

    assert xapi.run(list("case".split(" ")), exit_on_error=False) is True
    assert_called(case, 2)


def test_boolean_default_None():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[bool] = None):
        track_calls(case)
        return value

    with pytest.raises(SystemExit):
        assert xapi.run(list("case --value true".split(" "))) is True

    assert xapi.run(list("case --value".split(" ")), exit_on_error=False) is True

    assert xapi.run(list("case".split(" ")), exit_on_error=False) is False
    assert_called(case, 2)


def test_literal_multi_max():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Literal["min", "max"] = "min"):
        track_calls(case)
        return value

    assert xapi.run(list("case --value max".split(" ")), exit_on_error=False) == "max"
    assert xapi.run(list("case".split(" ")), exit_on_error=False) == "min"
    assert_called(case, 2)


def test_literal_multi_other():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Literal["min", "max"] = "min"):
        track_calls(case)
        return value

    with pytest.raises(SystemExit):
        xapi.run(list("case --value blah".split(" ")), exit_on_error=False)
    assert_called(case, 0)


def test_enum():
    xapi = XAPI()

    class TestEnum(Enum):
        a = "a"
        b = "b"
        c = "c"

    # print([k for k in vars(TestEnum) if not k[0] == "_"])

    @xapi.entrypoint
    def case(value: TestEnum = TestEnum.b):
        track_calls(case)
        return value.value

    assert xapi.run(list("case --value c".split(" ")), exit_on_error=False) == "c"
    assert xapi.run(list("case".split(" ")), exit_on_error=False) == "b"
    assert_called(case, 2)


def test_class_optional():
    xapi = XAPI()

    class TestCase:
        def __init__(self, text: str):
            # if text is None:  # type: ignore Testing to operation
            #     raise TypeError("text is a required parameter")
            self.test_data = text

    @xapi.entrypoint
    def case(value: Optional[TestCase] = None):
        track_calls(case)
        if not value:
            return None

        return value

    assert xapi.run(list("case --value blah".split(" "))).test_data == "blah"
    assert xapi.run(list("case".split(" "))) is None
    assert_called(case, 2)


def test_class_default():
    xapi = XAPI()

    class TestCase:
        def __init__(self, text: str):
            if text is None:  # type: ignore Testing to operation
                raise TypeError("text is a required parameter")
            self.test_data = text

    @xapi.entrypoint
    def case(value: Optional[TestCase] = None):
        track_calls(case)
        if not value:
            return None

        return value

    assert xapi.run(list("case --value blah".split(" "))).test_data == "blah"
    assert xapi.run(list("case".split(" "))) is None
    assert_called(case, 2)


def test_kwargs():
    xapi = XAPI()

    @xapi.entrypoint
    def case(**kwargs):  # type: ignore Testing to operation
        track_calls(case)
        return cast(dict[str, Any], kwargs)

    assert xapi.run(list("case --value blahblahblah --strip 2".split(" "))) == {
        "value": "blahblahblah",
        "strip": "2",
    }
    assert_called(case, 1)


def test_kwargs_with_args():
    xapi = XAPI()

    @xapi.entrypoint
    def case(*args, **kwargs):  # type: ignore Testing to operation
        track_calls(case)
        return cast(dict[str, Any], kwargs) | {"args": cast(list[Any], args)}

    assert xapi.run(list("case 1 2 3 --value blahblahblah --strip 2".split(" "))) == {
        "value": "blahblahblah",
        "strip": "2",
        "args": ("1", "2", "3"),
    }
    assert_called(case, 1)


def test_kwargs_with_other_args():
    xapi = XAPI()

    @xapi.entrypoint
    def case(a, *args, x=5, **kwargs):  # type: ignore Testing to operation
        track_calls(case)
        return cast(dict[str, Any], kwargs) | {
            "a": a,
            "args": cast(list[Any], args),
            "x": x,
        }

    assert xapi.run(
        list("case 10 1 2 3 --value blahblahblah --strip 2".split(" "))
    ) == {
        "value": "blahblahblah",
        "strip": "2",
        "a": "10",
        "args": ("1", "2", "3"),
        "x": 5,
    }
    assert_called(case, 1)


def test_unexpected_kwargs():
    xapi = XAPI()

    @xapi.entrypoint
    def not_called_case(**kwargs):  # type: ignore Testing to operation
        raise AssertionError("should not have been called")

    @xapi.entrypoint
    def case():
        track_calls(case)
        return "called"

    with pytest.raises(argparse.ArgumentError):
        assert xapi.run(
            list("case --value blahblahblah --strip 2".split(" ")),
            exit_on_error=False,
        )
    assert_called(case, 0)
