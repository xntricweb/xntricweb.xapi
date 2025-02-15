from enum import Enum
from typing import Literal

import pytest

from xntricweb.xapi.xapi import XAPI


def assert_called_once(fn):
    assert not hasattr(fn, "calls")
    fn.calls = 1


def test_no_args():
    xapi = XAPI()

    @xapi.entrypoint
    def no_args():
        assert_called_once(no_args)
        return 32423

    assert xapi.run(["no_args"]) == 32423


def test_basic_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def int_arg(value):
        assert_called_once(int_arg)
        return value

    assert xapi.run(["int_arg", "abc"], exit_on_error=False) == "abc"


def test_annotated_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def annotated_arg(value: int):
        assert_called_once(annotated_arg)
        return value

    assert xapi.run(["annotated_arg", "549"], exit_on_error=False) == 549


def test_var_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def var_arg(*value: int):
        assert_called_once(var_arg)
        return sum(value)

    assert xapi.run(["var_arg", "12", "14", "52"], exit_on_error=False) == 78


def test_list():
    xapi = XAPI()

    @xapi.entrypoint
    def list_entry(value: list):
        assert_called_once(list_entry)
        return value[0] + value[1] + value[2]

    assert (
        xapi.run(["list_entry", "13", "14", "52"], exit_on_error=False)
        == "131452"
    )


def test_list_int():
    xapi = XAPI()

    @xapi.entrypoint
    def list_int_entry(value: list[int]):
        assert_called_once(list_int_entry)
        return value[0] + value[1] + value[2]

    assert (
        xapi.run(["list_int_entry", "13", "14", "52"], exit_on_error=False)
        == 79
    )


def test_list_empty():
    xapi = XAPI()

    @xapi.entrypoint
    def list_empty_entry(value: list[int]):
        assert_called_once(list_empty_entry)
        return sum(value)

    assert xapi.run(["list_empty_entry"], exit_on_error=False) == 0


def test_tuple():
    xapi = XAPI()

    @xapi.entrypoint
    def tuple_entry(value: tuple):
        assert_called_once(tuple_entry)
        return f"{value}"

    assert (
        xapi.run(["tuple_entry", "13", "14", "52"], exit_on_error=False)
        == "('13', '14', '52')"
    )


def test_tuple_typed():
    xapi = XAPI()

    @xapi.entrypoint
    def tuple_typed_entry(value: tuple[str, int]):
        assert_called_once(tuple_typed_entry)
        return f"{value[0]}: {value[1]}"

    assert (
        xapi.run("tuple_typed_entry abc 123".split(" "), exit_on_error=False)
        == "abc: 123"
    )


def test_literal_single():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_single_entry(value: Literal["min"]):
        assert_called_once(lit_single_entry)
        return value

    with pytest.raises(AttributeError):
        assert (
            xapi.run("lit_single_entry min".split(" "), exit_on_error=False)
            == "min"
        )


def test_literal_multi_min():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_multi_min_entry(value: Literal["min", "max"]):
        assert_called_once(lit_multi_min_entry)
        return value

    assert (
        xapi.run("lit_multi_min_entry min".split(" "), exit_on_error=False)
        == "min"
    )


def test_literal_multi_max():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_multi_max_entry(value: Literal["min", "max"]):
        assert_called_once(lit_multi_max_entry)
        return value

    assert (
        xapi.run("lit_multi_max_entry max".split(" "), exit_on_error=False)
        == "max"
    )


def test_literal_multi_other():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_multi_other_entry(value: Literal["min", "max"]):
        assert_called_once(lit_multi_other_entry)
        return value

    with pytest.raises(SystemExit):
        xapi.run("lit_multi_other_entry blah".split(" "), exit_on_error=False)


def test_enum():
    xapi = XAPI()

    class TestEnum(Enum):
        a = "a"
        b = "b"
        c = "c"

    print([k for k in vars(TestEnum) if not k[0] == "_"])

    @xapi.entrypoint
    def enum_entry(value: TestEnum):
        assert_called_once(enum_entry)
        return value.value

    assert xapi.run("enum_entry a".split(" "), exit_on_error=False) == "a"


def test_boolean():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: bool):
        # assert_called_once(case)
        return value

    with pytest.raises(SystemExit):
        assert xapi.run("case true".split(" ")) is True

    with pytest.raises(SystemExit):
        assert xapi.run("case --value true".split(" ")) is True

    assert xapi.run("case --value".split(" "), exit_on_error=False) is True

    assert xapi.run("case".split(" "), exit_on_error=False) is False
