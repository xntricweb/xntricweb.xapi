from .xapi import XAPI
from .entrypoint import Entrypoint
from .arguments import Argument

__version__ = "0.1.6"

__all__ = ["Entrypoint", "Argument", "setup", "XAPI"]

xapi = XAPI()
