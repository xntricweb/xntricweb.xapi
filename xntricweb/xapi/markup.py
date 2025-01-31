import typing

Tag = typing.Annotated


class _Annotation:
    name: str
    value: typing.Any

    # def __init__(self, value: T):
    #     self.name = (
    #         self.name
    #         if hasattr(self, "name")
    #         else self.__class__.__name__.lower()
    #     )

    #     self.value = value

    def __class_get_item__(val):
        return "test"


def x(a: _Annotation["test"]):
    pass


class Annotation[T]:
    name: str
    value: T

    def __init__(self, value: T):
        self.name = (
            self.name
            if hasattr(self, "name")
            else self.__class__.__name__.lower()
        )

        self.value = value


class Name(Annotation[str]):
    """Name for parse args"""


class Alias(Annotation[tuple]):
    """Aliases for parse args."""

    def __init__(self, *args: str):
        """Initialize the class with the provided value for alias."""
        super().__init__(args)


class Action(Annotation[str]):
    """Action for parse args"""


class NArgs(Annotation[str | int]):
    """Number of args for parse args."""

    def __init__(self, value: typing.Literal["*", "?", "+"] | int):
        """Initialize the class with the provided value for nargs."""
        super().__init__(value)


class Const[T](Annotation[T]):
    """Const for parse args"""


class Default[T](Annotation[T]):
    """Default for parse args"""


class Type[T](Annotation[T]):
    """Default for parse args"""


class Choices(Annotation[list[str]]):
    """Default for parse args"""

    def __init__(self, *args: str):
        super().__init__(args)


class Required(Annotation[bool]):
    """Required for parse args"""


class Help(Annotation[str]):
    """Help for parse args"""


class Metavar(Annotation[str]):
    """Metavar for parse args"""


class Dest(Annotation[str]):
    """Dest for parse args"""


class Deprecated(Annotation[bool]):
    """Deprecated for parse args"""
