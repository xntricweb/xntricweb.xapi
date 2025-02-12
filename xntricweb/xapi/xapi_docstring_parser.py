from typing import Callable, Optional
from .const import log

try:
    import docstring_parser as parser
except ImportError:
    log.warning(
        "could not import docstring_parser, install it to supplement xapi "
        "command information"
    )
    parser = None


class DocInfo:

    def __init__(self, fn: Optional[Callable]):
        self.doc_info = self.get_doc_info(fn)

    def get_doc_info(self, fn: Optional[Callable]):
        if not fn:
            return None

        if not parser:
            return None

        if not hasattr(fn, "__doc__"):
            log.debug("%r has no __doc__ information to parse", fn)
            return None

        info = parser.parse(fn.__doc__)
        log.debug("found doc_info %r: %r", fn, vars(info))

        return info

    def get_argument_doc_info(self, index: int):
        if not (self.doc_info):
            return {}

        if index >= len(self.doc_info.params):
            return {}

        doc_info = self.doc_info.params[index]
        info = {"help": doc_info.description}
        log.debug(
            "processed argument doc info %r with %r", info, vars(doc_info)
        )
        return info

    def get_entrypoint_doc_info(self):
        if not self.doc_info:
            return {}
        doc_info = self.doc_info

        info = {
            "description": "\n".join(
                [
                    doc_info.short_description or "",
                    doc_info.long_description or "",
                ]
            ),
        }
        log.debug("processed entrypoint doc info %r", info)

        return info
