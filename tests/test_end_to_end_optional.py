import argparse
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

import pytest

from xntricweb.xapi.xapi import XAPI


def assert_called_once(fn):
    # assert not hasattr(fn, "calls")
    fn.calls = 1


def test_no_args():
    xapi = XAPI()

    @xapi.entrypoint
    def case():
        assert_called_once(case)
        return 32423

    assert xapi.run(["case"]) == 32423


def test_optional_string():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[str] = None):
        assert_called_once(case)
        return value

    assert xapi.run("case --value abc".split(" ")) == "abc"
    assert xapi.run("case".split(" ")) is None


def test_basic_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value="5"):
        assert_called_once(case)
        return value

    assert xapi.run(["case", "--value", "abc"], exit_on_error=False) == "abc"
    assert xapi.run(["case"], exit_on_error=False) == "5"


def test_datetime():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[datetime] = None):
        assert_called_once(case)
        return value and value.isoformat()

    assert (
        xapi.run(["case", "--value", "2025-02-16T22:00"], exit_on_error=False)
        == "2025-02-16T22:00:00"
    )
    assert xapi.run(["case"], exit_on_error=False) is None


def test_annotated_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: int = 4):
        assert_called_once(case)
        return value

    assert xapi.run(["case", "--value", "549"], exit_on_error=False) == 549
    assert xapi.run(["case"], exit_on_error=False) == 4


def test_list_optional():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[list] = None):
        assert_called_once(case)
        return "".join(value or [])

    assert (
        xapi.run("case --value 13 14 52".split(" "), exit_on_error=False)
        == "131452"
    )
    assert xapi.run(["case"], exit_on_error=False) == ""


def test_list_union():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: list | None = None):
        assert_called_once(case)
        return "".join(value or [])

    assert (
        xapi.run(["case", "--value", "13", "14", "52"], exit_on_error=False)
        == "131452"
    )
    assert xapi.run(["case"], exit_on_error=False) == ""


def test_list_int():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[list[int]] = None):
        assert_called_once(case)
        return sum(value or [])

    assert (
        xapi.run(
            ["case", "--value", "13", "14", "52"],
            exit_on_error=False,
        )
        == 79
    )
    assert xapi.run(["case"], exit_on_error=False) == 0


def test_list_empty():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[list[int]] = None):
        assert_called_once(case)
        return sum(value or [])

    assert xapi.run(["case", "--value"], exit_on_error=False) == 0
    assert xapi.run(["case"], exit_on_error=False) == 0


def test_tuple():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[tuple] = None):
        assert_called_once(case)
        return f"{value or tuple()}"

    assert (
        xapi.run(["case", "--value", "13", "14", "52"], exit_on_error=False)
        == "('13', '14', '52')"
    )

    assert xapi.run(["case"], exit_on_error=False) == "()"


def test_tuple_typed():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[tuple[str, int]] = None):
        assert_called_once(case)
        if not value:
            return
        return f"{':'.join([str(v) for v in value] or [])}"

    assert (
        xapi.run("case --value abc 123".split(" "), exit_on_error=False)
        == "abc:123"
    )
    assert xapi.run("case".split(" "), exit_on_error=False) is None


def test_literal_single():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Literal["min"] = None):
        assert_called_once(case)
        return value

    with pytest.raises(AttributeError):
        assert xapi.run("case min".split(" "), exit_on_error=False) == "min"


def test_literal_multi_min():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[Literal["min", "max"]] = "max"):
        assert_called_once(case)
        return value

    assert (
        xapi.run("case --value min".split(" "), exit_on_error=False) == "min"
    )

    assert xapi.run("case".split(" "), exit_on_error=False) == "max"


def test_literal_multi_min_optional():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[Literal["min", "max"]] = None):
        assert_called_once(case)
        return value

    assert (
        xapi.run("case --value min".split(" "), exit_on_error=False) == "min"
    )

    assert xapi.run("case".split(" "), exit_on_error=False) is None


def test_boolean_default_false():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[bool] = False):
        assert_called_once(case)
        return value

    with pytest.raises(SystemExit):
        assert xapi.run("case --value true".split(" ")) is True

    assert xapi.run("case --value".split(" "), exit_on_error=False) is True

    assert xapi.run("case".split(" "), exit_on_error=False) is False


def test_boolean_default_true():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[bool] = True):
        assert_called_once(case)
        return value

    with pytest.raises(argparse.ArgumentError):
        assert (
            xapi.run("case --value true".split(" "), exit_on_error=False)
            is True
        )

    assert xapi.run("case --value".split(" "), exit_on_error=False) is False

    assert xapi.run("case".split(" "), exit_on_error=False) is True


def test_boolean_default_None():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Optional[bool] = None):
        assert_called_once(case)
        return value

    with pytest.raises(SystemExit):
        assert xapi.run("case --value true".split(" ")) is True

    assert xapi.run("case --value".split(" "), exit_on_error=False) is True

    assert xapi.run("case".split(" "), exit_on_error=False) is False


def test_literal_multi_max():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Literal["min", "max"] = "min"):
        assert_called_once(case)
        return value

    assert (
        xapi.run("case --value max".split(" "), exit_on_error=False) == "max"
    )
    assert xapi.run("case".split(" "), exit_on_error=False) == "min"


def test_literal_multi_other():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: Literal["min", "max"] = "min"):
        assert_called_once(case)
        return value

    with pytest.raises(SystemExit):
        xapi.run("case --value blah".split(" "), exit_on_error=False)


def test_enum():
    xapi = XAPI()

    class TestEnum(Enum):
        a = "a"
        b = "b"
        c = "c"

    # print([k for k in vars(TestEnum) if not k[0] == "_"])

    @xapi.entrypoint
    def case(value: TestEnum = TestEnum.b):
        assert_called_once(case)
        return value.value

    assert xapi.run("case --value c".split(" "), exit_on_error=False) == "c"
    assert xapi.run("case".split(" "), exit_on_error=False) == "b"


def test_class_optional():
    xapi = XAPI()

    class TestCase:
        def __init__(self, text: str):
            if text is None:
                raise TypeError("text is a required parameter")
            self.test_data = text

    @xapi.entrypoint
    def case(value: Optional[TestCase] = None):
        if not value:
            return None

        return value

    assert xapi.run("case --value blah".split(" ")).test_data == "blah"
    assert xapi.run("case".split(" ")) is None


def test_class_default():
    xapi = XAPI()

    class TestCase:
        def __init__(self, text: str):
            if text is None:
                raise TypeError("text is a required parameter")
            self.test_data = text

    @xapi.entrypoint
    def case(value: Optional[TestCase] = None):
        if not value:
            return None

        return value

    assert xapi.run("case --value blah".split(" ")).test_data == "blah"
    assert xapi.run("case".split(" ")) is None


def test_kwargs():
    xapi = XAPI()

    @xapi.entrypoint
    def case(**kwargs):
        assert_called_once(case)
        return kwargs

    assert xapi.run("case --value blahblahblah --strip 2".split(" ")) == {
        "value": "blahblahblah",
        "strip": "2",
    }


def test_kwargs_with_args():
    xapi = XAPI()

    @xapi.entrypoint
    def case(*args, **kwargs):
        assert_called_once(case)
        return kwargs | {"args": list(args)}

    assert xapi.run(
        "case 1 2 3 --value blahblahblah --strip 2".split(" ")
    ) == {
        "value": "blahblahblah",
        "strip": "2",
        "args": ["1", "2", "3"],
    }


def test_kwargs_with_other_args():
    xapi = XAPI()

    @xapi.entrypoint
    def case(a, *args, x=5, **kwargs):
        assert_called_once(case)
        return kwargs | {"a": a, "args": list(args), "x": x}

    assert xapi.run(
        "case 10 1 2 3 --value blahblahblah --strip 2".split(" ")
    ) == {
        "value": "blahblahblah",
        "strip": "2",
        "a": "10",
        "args": ["1", "2", "3"],
        "x": 5,
    }


def test_unexpected_kwargs():
    xapi = XAPI()

    @xapi.entrypoint
    def not_called_case(**kwargs):
        raise AssertionError("should not have been called")

    @xapi.entrypoint
    def case():
        assert_called_once(case)
        return "called"

    with pytest.raises(argparse.ArgumentError):
        assert xapi.run(
            "case --value blahblahblah --strip 2".split(" "),
            exit_on_error=False,
        )
