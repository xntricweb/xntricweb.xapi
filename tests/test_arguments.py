import pytest
from xntricweb.xapi.arguments import Argument, _convert, ConversionError


def upper(str):
    return str.upper()


def _generate_arg(arg, value):
    args = []
    kwargs = {}
    arg.generate_call_arg(value, args, kwargs)
    return args, kwargs


def test_converters():
    assert _convert("1", int) == 1
    assert _convert("1", list[int]) == [1]
    assert _convert([1], str) == "[1]"
    assert _convert("2", tuple[str]) == ("2",)
    with pytest.raises(ConversionError):
        assert _convert("a", int)

    with pytest.raises(ConversionError):
        assert _convert([1], int)


test_cases = [
    ((Argument("name_only", index=0), "blah"), (["blah"], {})),
    (
        (Argument("fn_annotation", index=0, annotation=upper), "blah"),
        (["BLAH"], {}),
    ),
    (
        (Argument("vararg", index=0, vararg=True), ["blah", "blah"]),
        (["blah", "blah"], {}),
    ),
    ((Argument("default_passed", default="blah"), "blah"), ([], {})),
    (
        (Argument("default_different", default="blah"), "bang"),
        ([], {"default_different": "bang"}),
    ),
    (
        (Argument("annotated_different", index=0, annotation=int), "1"),
        ([1], {}),
    ),
    (
        (
            Argument(
                "annotated_tuple", index=0, annotation=tuple[str, int, float]
            ),
            ["1.3", "4", "5.2"],
        ),
        ([("1.3", 4, 5.2)], {}),
    ),
    (
        (Argument("annotated_kw_diff", annotation=int, default=2), "1"),
        ([], {"annotated_kw_diff": 1}),
    ),
    (
        (
            Argument("annotated_list", index=0, annotation=list[str]),
            ["1", "2"],
        ),
        ([["1", "2"]], {}),
    ),
    (
        (
            Argument("annotated_list_conv", index=0, annotation=list[int]),
            ["1", "2"],
        ),
        ([[1, 2]], {}),
    ),
    (
        (
            Argument(
                "annotated_kw_list_conv",
                annotation=list[int],
                default=None,
            ),
            ["1", "2"],
        ),
        ([], {"annotated_kw_list_conv": [1, 2]}),
    ),
    (
        (
            Argument(
                "annotated_kw_list_conv",
                annotation=list[int],
                default=None,
            ),
            ["1", "2"],
        ),
        ([], {"annotated_kw_list_conv": [1, 2]}),
    ),
    (
        (Argument("var_kwarg", index=None, vararg=True), {"blah": "1"}),
        ([], {"blah": "1"}),
    ),
]


@pytest.mark.parametrize(
    "case, expected", test_cases, ids=[tc[0][0].name for tc in test_cases]
)
def test_cases(case, expected):
    # case, expected = test_case
    # for case, expected in basic_test_cases:
    actual = _generate_arg(*case)
    assert actual == expected, f"{case} failed"
