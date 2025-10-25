from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from types import UnionType
from typing import Any, Callable, Literal, Optional, Protocol, Union

from xntricweb.xapi.utility import get_origin_args

from .const import NOT_SPECIFIED, AnyType, NotSpecified, log


@dataclass
class Argument[T]:
    """Describes a method argument."""

    name: str
    """The argument name."""

    annotation: Optional[Callable[[str], T]] = None
    """
    The arguments annotation type. 
    This must be a Callable and will be used to coerce the value to the 
    correct type for the function.
    """

    index: Optional[int] = None
    """
    The positional index of the argument. If the argument is keyword
    only it should be set to None.
    """

    default: T | NotSpecified = NOT_SPECIFIED
    """
    The default value of the argument. If NOT_SPECIFIED then the
    argument is considered required.
    """

    vararg: Optional[bool] = None
    """
    Whether the argument is a vararg type of argument... e.g. *args, **kwargs
    """

    aliases: Optional[list[str]] = None
    help: Optional[str] = None
    metavar: Optional[str] = None

    def generate_call_arg(
        self,
        value: Any,
        args: Optional[list[Any]] = None,
        kwargs: Optional[dict[str, Any]] = None,
    ):
        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        log.debug("generating call args for %r with value %r", self, value)

        if self.vararg:
            if self.index is not None:
                _value = _convert(value, list[self.annotation])
                log.debug(
                    "generated varargs for %r with value %r", self, _value
                )
                args.extend(_value)
                return args, kwargs

            _value = _convert(value, dict)
            log.debug("generating kwargs for %r: %r", self.name, _value)
            kwargs.update(_value)
            return args, kwargs

        _value = _convert(value, self.annotation)
        if self.index is not None and self.default is NOT_SPECIFIED:
            log.debug(
                "generating positional for %r with value %r", self, _value
            )
            args.append(_value)
            return args, kwargs

        if _value != self.default:

            log.debug(
                "generating kwarg for %r with value %r", self.name, _value
            )
            kwargs[self.name] = _value
            return args, kwargs

        log.debug("no call args generated for %r with value %r", self, _value)
        return args, kwargs

    def __str__(self):
        r = ""
        if self.vararg:
            if self.index is None:
                r += "**"
            else:
                r += "*"

        r += self.name
        if self.annotation:
            r += f":{self.annotation}"
        if self.default is not NOT_SPECIFIED:
            r += f"={repr(self.default)}"
        return r

    # def __repr__(self):
    #     parts = [
    #         f"{k}={v}"
    #         for k, v in vars(self).items()
    #         if k != "default" and not (v is None or k[0] == ("_"))
    #     ]
    #     if self.default is not NOT_SPECIFIED:
    #         parts.append(f"default={self.default}")
    #     return f"{self.__class__.__name__}({', '.join(parts)})"


class ConversionError(TypeError):
    """The error that is raised when value conversion fails."""


class _Converter[T](Protocol):
    def __call__(
        self,
        *,
        value: Any,
        origin: AnyType,
        origin_args: tuple[AnyType, ...],
        annotation: AnyType,
    ) -> T:
        raise NotImplementedError()


def _default_type_converter(
    value: Any, origin: AnyType, origin_args: tuple[AnyType, ...], **_: Any
) -> Any:
    log.debug(
        "using default type converter for %r with %r[%r]",
        value,
        origin,
        origin_args,
    )

    if callable(origin):
        return origin(value)

    raise ConversionError(
        f"Unsupported origin {origin}, origin must be callable"
    )


def _function_type_converter(value: Any, annotation: AnyType, **_: Any) -> Any:
    log.debug(
        "Using function type converter for %r with annotations: %r",
        value,
        annotations,
    )
    if callable(annotation):
        return annotation(value)

    raise ConversionError(
        f"Failed converting {value} to {annotation} for "
        f"Callable[[...], Any] -> {annotation}:"
    )


def _iterable_type_converter(
    value: Any, origin: AnyType, origin_args: tuple[AnyType, ...], **_: Any
) -> list[Any] | tuple[Any, ...] | None:
    params = None
    if not origin_args or len(origin_args) == 0:
        return _default_type_converter(value, origin, origin_args)
    elif len(origin_args) == 1:
        if value is None:
            _v = _convert(value, origin_args[0])
            if _v:
                return [_v]
            return None

            # return [_convert(value, origin_args)]
        params = [_convert(sub_value, origin_args[0]) for sub_value in value]

    elif len(origin_args) > 1:
        if len(origin_args) != len(value):
            raise ConversionError(
                f"annotation expected {len(origin_args)} items..."
                f" found {len(value)}"
            )

        log.debug("converting %r")
        params = [
            _convert(sub_value, origin_args[index])
            for index, sub_value in enumerate(value)
        ]

    if callable(origin) and params:
        return origin(params)

    raise ConversionError(
        f"Unsupported origin {origin}({params}), origin must be callable"
    )


def _literal_type_converter(
    value: Any, origin_args: tuple[AnyType, ...], **_: Any
):
    if value in origin_args:
        return value
    raise TypeError(f"Expected {origin_args} found '{type(value)}'")


def _datetime_type_converter(value: str | None, **_) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _union_type_converter(
    value: Any, origin_args: tuple[AnyType, ...], **_: Any
):
    if value is None and None.__class__ in origin_args:
        return None

    for _type in origin_args:
        try:
            return _convert(value, _type)
            # return _type(value)
        except Exception:
            pass

    raise ConversionError("Unable to convert value %s" % value)


def _dict_type_converter(
    value: Any,
    origin: AnyType,
    origin_args: tuple[AnyType, ...],
    **_: Any,
):
    if value is None and None.__class__ in origin_args:
        return None

    if isinstance(value, str):
        value = json.loads(value)

    if not origin_args:
        return _default_type_converter(value, origin, origin_args)

    raise ConversionError()


type_converters: dict[AnyType, _Converter[Any]] = {
    Union: _union_type_converter,
    UnionType: _union_type_converter,
    Literal: _literal_type_converter,
    dict: _dict_type_converter,
    list: _iterable_type_converter,
    tuple: _iterable_type_converter,
    datetime: _datetime_type_converter,
    _function_type_converter.__class__.__base__: _function_type_converter,
}


def _get_converter(
    origin: AnyType, default: Any = None
) -> _Converter[Any] | None:
    base = None
    converter = type_converters.get(origin, None)
    if not converter:
        log.debug("searching base converters for origin: %r", origin)
        _bases = getattr(origin, "__bases__", None)
        if _bases:
            for base in reversed(_bases):
                converter = type_converters.get(base)
                if converter:
                    break
        else:
            _class = getattr(origin, "__class__")
            log.debug("found %r class for origin %r", _class, origin)
            origin = _class
    log.debug(
        "found converter %r using base %r for origin %r",
        converter,
        base,
        origin,
    )
    return converter


def _convert(value: Any, annotation: AnyType):
    log.debug("Attempting conversion for %r as %r", value, annotation)
    if not annotation or annotation is None.__class__:
        return value

    origin, origin_args = get_origin_args(annotation)
    converter = _get_converter(origin)

    if not converter:
        converter = _default_type_converter

    log.debug(
        "converting value '%r' using %r with origin: %r, args: %r",
        value,
        getattr(converter, "__name__", "[N/A]"),
        origin,
        origin_args,
    )

    try:
        return converter(
            value=value,
            origin=origin,
            origin_args=origin_args,
            annotation=annotation,
        )
    except Exception as e:
        raise ConversionError(
            "Failed converting %r with %r, annotation: %r"
            % (value, origin, annotation)
        ) from e
