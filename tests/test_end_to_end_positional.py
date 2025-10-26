from enum import Enum
from typing import Any, Callable, Literal
import pytest

from xntricweb.xapi.xapi import XAPI


def track_calls(fn: Callable[..., Any]):
    setattr(fn, "_calls", getattr(fn, "_calls", 0) + 1)


def calls(fn: Callable[..., Any]):
    return getattr(fn, "_calls", 0)


def test_no_args():
    xapi = XAPI()

    @xapi.entrypoint
    def no_args():
        track_calls(no_args)
        return 32423

    assert xapi.run(["no_args"]) == 32423
    assert calls(no_args) == 1


def test_basic_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def int_arg(value):  # type: ignore
        track_calls(int_arg)
        return value  # type: ignore

    assert xapi.run(["int_arg", "abc"], exit_on_error=False) == "abc"
    assert calls(int_arg) == 1


def test_annotated_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def annotated_arg(value: int):
        track_calls(annotated_arg)
        return value

    assert xapi.run(["annotated_arg", "549"], exit_on_error=False) == 549
    assert calls(annotated_arg) == 1


def test_var_arg():
    xapi = XAPI()

    @xapi.entrypoint
    def var_arg(*value: int):
        track_calls(var_arg)
        return sum(value)

    assert xapi.run(["var_arg", "12", "14", "52"], exit_on_error=False) == 78
    assert calls(var_arg) == 1


def test_list():
    xapi = XAPI()

    @xapi.entrypoint
    def list_entry(value: list[Any]):  # type: ignore
        track_calls(list_entry)
        return value[0] + value[1] + value[2]  # type: ignore

    assert xapi.run(["list_entry", "13", "14", "52"], exit_on_error=False) == "131452"
    assert calls(list_entry) == 1


def test_list_int():
    xapi = XAPI()

    @xapi.entrypoint
    def list_int_entry(value: list[int]):
        track_calls(list_int_entry)
        return value[0] + value[1] + value[2]

    assert xapi.run(["list_int_entry", "13", "14", "52"], exit_on_error=False) == 79
    assert calls(list_int_entry) == 1


def test_list_empty():
    xapi = XAPI()

    @xapi.entrypoint
    def list_empty_entry(value: list[int]):
        track_calls(list_empty_entry)
        return sum(value)

    assert xapi.run(["list_empty_entry"], exit_on_error=False) == 0
    assert calls(list_empty_entry) == 1


def test_tuple():
    xapi = XAPI()

    @xapi.entrypoint
    def tuple_entry(value: tuple):  # type: ignore
        track_calls(tuple_entry)
        return f"{value}"

    assert (
        xapi.run(["tuple_entry", "13", "14", "52"], exit_on_error=False)
        == "('13', '14', '52')"
    )
    assert calls(tuple_entry) == 1


def test_tuple_typed():
    xapi = XAPI()

    @xapi.entrypoint
    def tuple_typed_entry(value: tuple[str, int]):
        track_calls(tuple_typed_entry)
        return f"{value[0]}: {value[1]}"

    assert (
        xapi.run(list("tuple_typed_entry abc 123".split(" ")), exit_on_error=False)
        == "abc: 123"
    )
    assert calls(tuple_typed_entry) == 1


def test_literal_single():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_single_entry(value: Literal["min"]):
        track_calls(lit_single_entry)
        return value

    # with pytest.raises(AttributeError):
    #     assert xapi.run(list("lit_single_entry min".split(" ")), exit_on_error=False) == "min"
    assert (
        xapi.run(list("lit_single_entry min".split(" ")), exit_on_error=False) == "min"
    )
    assert calls(lit_single_entry) == 1


def test_literal_multi_min():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_multi_min_entry(value: Literal["min", "max"]):
        track_calls(lit_multi_min_entry)
        return value

    assert (
        xapi.run(list("lit_multi_min_entry min".split(" ")), exit_on_error=False)
        == "min"
    )
    assert calls(lit_multi_min_entry) == 1


def test_literal_multi_max():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_multi_max_entry(value: Literal["min", "max"]):
        track_calls(lit_multi_max_entry)
        return value

    assert (
        xapi.run(list("lit_multi_max_entry max".split(" ")), exit_on_error=False)
        == "max"
    )
    assert calls(lit_multi_max_entry) == 1


def test_literal_multi_other():
    xapi = XAPI()

    @xapi.entrypoint
    def lit_multi_other_entry(value: Literal["min", "max"]):
        track_calls(lit_multi_other_entry)
        return value

    with pytest.raises(SystemExit):
        xapi.run(list("lit_multi_other_entry blah".split(" ")), exit_on_error=False)
    assert calls(lit_multi_other_entry) == 0


def test_enum():
    xapi = XAPI()

    class TestEnum(Enum):
        a = "a"
        b = "b"
        c = "c"

    print([k for k in vars(TestEnum) if not k[0] == "_"])

    @xapi.entrypoint
    def enum_entry(value: TestEnum):
        track_calls(enum_entry)
        return value.value

    assert xapi.run(list("enum_entry a".split(" ")), exit_on_error=False) == "a"
    assert calls(enum_entry) == 1


def test_boolean():
    xapi = XAPI()

    @xapi.entrypoint
    def case(value: bool):
        track_calls(case)
        return value

    with pytest.raises(SystemExit):
        assert xapi.run(list("case true".split(" "))) is True

    with pytest.raises(SystemExit):
        assert xapi.run(list("case --value true".split(" "))) is True

    assert xapi.run(list("case --value".split(" ")), exit_on_error=False) is True

    assert xapi.run(list("case".split(" ")), exit_on_error=False) is False
    assert calls(case) == 2
