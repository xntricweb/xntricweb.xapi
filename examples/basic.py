"""
A basic application that has a few math functions.
"""

import argparse
from typing import Optional
from xntricweb.xapi import XAPI

import random
import logging

# logging.basicConfig(level=logging.DEBUG)
xapi = XAPI()


@xapi.effect
def setup_logging(log_level: str = "WARNING"):
    """
    Configures the logging level of the application.

    Parameters
    ----------
    log_level : str
        The log level to set.
    """
    logging.basicConfig(
        level=logging.getLevelNamesMapping().get(
            log_level.upper(), logging.WARNING
        )
    )


@xapi.effect
def print_stuff():
    print("stuff")


Math = xapi.entrypoint("math")()
boop = xapi.entrypoint("boop", parent=Math)()


@xapi.entrypoint
def test_parent(name: Optional[str] = "John Doe"):
    """
    A parent entrypoint test.
    Parameters
    ----------
        name:Optional[str] The identity
    """
    if not name:
        name = "john doe"
    print(f"hello {name} from test parent")


@xapi.entrypoint(name="test", parent=test_parent)
def sub(
    term: float, subtrahend: float, *subtrahends: float, precision: int = 2
):
    """Performs subtraction operations.
    :param term:float The minuend to subtract from.
    :param subtrahend:float The subtrahend to subtract from the minuend.
    :param subtrahends:list[float] Additional subtrahends to subtract
        from the minuend.
    """
    print(round(term - subtrahend - (sum(subtrahends)), 2))
    return 0


@xapi.entrypoint
def pick(count: int, *words: str, upper: bool = True):
    while count > 0:
        count -= 1
        text = random.choice(words)
        if upper:
            text = text.upper()
        print(text)

    return 0


@xapi.entrypoint
def blah():
    print("blah")


@xapi.entrypoint
def add(
    addend1: float,
    addend2: float,
    precision: int = 1,
):
    """
    Adds the two input numbers together.

    :param float addend1: The first addend
    :param float addend2: The second addend
    :returns float The sum of the first and second addend's
    """
    _sum = round(addend1 + addend2, precision)
    return _sum


@xapi.entrypoint
def summ(*args: float, precision: int = 2):
    """
    Sums the provided input numbers.

    Adds all of the numbers provided and outputs the results.

    Parameters
    ----------
    args : float
        The values to sum.
    precision : int
        The precision of the output.
    """
    _sum = round(sum(args), precision)
    print(_sum)
    return 1


xapi.run(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
