"""
A basic application that has a few math functions.
"""

from xntricweb.xapi import effect, Entrypoint, entrypoint, run, Argument

import random
import logging

# logging.basicConfig(level=logging.DEBUG)


@effect
def setup_logging(log_level: str = "WARNING"):
    logging.basicConfig(
        level=logging.getLevelNamesMapping().get(
            log_level.upper(), logging.WARNING
        )
    )


@effect
def print_stuff():
    print("stuff")


def sub(
    term: float, subtrahend: float, *subtrahends: float, precision: int = 2
):

    print(round(term - subtrahend - (sum(subtrahends)), 2))
    return 0


sub_entrypoint = Entrypoint(
    entrypoint=sub,
    name="subtract",
    aliases=["-"],
    help="Subtracts the second number from the first.",
    arguments=[
        Argument(
            name="minuend",
            annotation=float,
            help="The minuend to be subtracted from.",
            required=True,
        ),
        Argument(
            name="subtrahend",
            annotation=float,
            help="The subtrahend to subtract from the minuend",
            required=True,
        ),
        Argument(
            name="precision",
            annotation=int,
            help="The precision the result is displayed with.",
            default=2,
        ),
    ],
)


def pick(count: int, *words: str, upper: bool = True):
    while count > 0:
        count -= 1
        text = random.choice(words)
        if upper:
            text = text.upper()
        print(text)

    return 0


pick_entrypoint = Entrypoint(
    entrypoint=pick,
    help="Picks random words from a list of words",
    arguments=[
        Argument(
            name="count", annotation=int, help="The number of words to pick"
        ),
        Argument(
            name="words",
            annotation=str,
            help="The words to pick from",
            vararg=True,
        ),
        Argument(
            name="upper",
            annotation=bool,
            help="Causes the the output words to be capitalized.",
            default=True,
        ),
    ],
)


@entrypoint
def blah():
    print("blah")


@entrypoint
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
    print(_sum)
    return _sum


@entrypoint
def summ(*args: float, precision: int = 2):
    """
    Sums the provided input numbers.
    :param float addend1
    """
    _sum = round(sum(args), precision)
    print(_sum)
    return 1


run()
