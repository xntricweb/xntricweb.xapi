import logging
from typing import Any

log = logging.getLogger("xntricweb.xapi")


class _NotSpecified:
    __slots__: tuple[Any, ...] = tuple()

    def __str__(self):
        return "[Not Specified]"

    def __repr__(self):
        return "[Not Specified]"


NOT_SPECIFIED = _NotSpecified()
