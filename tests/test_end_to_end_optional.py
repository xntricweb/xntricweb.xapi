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


def test_basic_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value="5"):
        assert_called_once(case)
        return value

    assert xapi.run(["case", "--value", "abc"], exit_on_error=False) == "abc"
    assert xapi.run(["case"], exit_on_error=False) == "5"


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
            return ""
        return f"{':'.join([str(v) for v in value] or [])}"

    assert (
        xapi.run("case --value abc 123".split(" "), exit_on_error=False)
        == "abc:123"
    )
    assert xapi.run("case".split(" "), exit_on_error=False) == ""


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
    def case(value: Literal["min", "max"]):
        assert_called_once(case)
        return value

    assert xapi.run("case min".split(" "), exit_on_error=False) == "min"


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
