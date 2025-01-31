from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, Type


@dataclass
class Argument:
    name: Optional[str] = None
    annotation: Optional[Callable] = None
    index: Optional[int] = None
    default: Optional[bool] = None
    required: Optional[bool] = False

    aliases: Optional[list[str]] = None
    vararg: Optional[bool] = False
    help: Optional[str] = None
    metavar: Optional[str] = None

    def apply_arg_details(
        self, index: int, name: str, default: Any, annotation: Type
    ):
        self.index = index
        self.name = name
        self.default = default
        self.annotation = annotation
        self.required = True

    def generate_call_arg(
        self, value: Any, args: list[Any], kwargs: dict[str, Any]
    ):
        converter = self.annotation or str

        if self.vararg:
            args.extend(map(converter, value))
            return

        if self.required:
            args.append(converter(value))
            return

        if value != self.default:
            kwargs[self.name] = converter(value)

        return converter(value)
