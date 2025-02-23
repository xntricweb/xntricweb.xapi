import pytest
from xntricweb.xapi.xapi import XAPI


def test_entrypoint_is_callable():
    xapi = XAPI()

    @xapi.entrypoint
    def test_callable(x: int, y: int = 2):
        assert x == 10 and y == 2
        return 4

    assert test_callable(10) == 4


def test_get_entrypoint():
    xapi = XAPI()

    @xapi.effect()
    def effect_entry():
        pass

    @xapi.entrypoint()
    def named_entrypoint():
        pass

    @xapi.entrypoint(aliases=["aliased"])
    def aliased_entrypoint():
        pass

    assert xapi.get_entrypoint("effect_entry") is effect_entry
    assert xapi.get_entrypoint("named_entrypoint") is named_entrypoint
    assert xapi.get_entrypoint("aliased_entrypoint") is aliased_entrypoint
    assert xapi.get_entrypoint("aliased") is aliased_entrypoint

    with pytest.raises(KeyError):
        assert xapi.get_entrypoint("missing")
