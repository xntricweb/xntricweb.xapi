import logging

log = logging.getLogger("xntricweb.xapi")


class _NotSpecified:
    __slots__ = tuple()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "[Not Specified]"


NOT_SPECIFIED = _NotSpecified()
