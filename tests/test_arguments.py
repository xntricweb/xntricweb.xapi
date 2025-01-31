import xntricweb.xapi as xapi


def test_argument_basic():
    arg = xapi.Argument()

    args = []
    kwargs = {}
    arg.generate_call_arg("blah", args, kwargs)

    print(args, kwargs)

    assert False
