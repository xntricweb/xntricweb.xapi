import logging
from types import UnionType
from typing import Any, Type

log = logging.getLogger("xntricweb.xapi")

type AnyType = type | UnionType | Type[Any]


class _NotSpecified:
    __slots__: tuple[Any, ...] = tuple()

    def __str__(self):
        return "[Not Specified]"

    def __repr__(self):
        return "[Not Specified]"


NOT_SPECIFIED = _NotSpecified()
