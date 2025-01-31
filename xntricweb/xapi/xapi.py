"""
Terminal API tools
"""

from __future__ import annotations

import argparse
import inspect
import typing

from .entrypoint import Entrypoint
from .arguments import Argument


def _parse_annotations(entrypoint: typing.Callable):
    anno = inspect.getfullargspec(entrypoint)

    return {
        "name": entrypoint.__name__,
    }, {entry["name"]: entry for entry in _parse_annotation_arguments(anno)}


def _parse_doc_into(entrypoint: typing.Callable):
    return {}, {}


def _make_entrypoint_def(entrypoint: typing.Callable):
    ae, aa = _parse_annotations(entrypoint)
    de, da = _parse_doc_into(entrypoint)
    # unique_keys = {k: None for k in [*aa.keys(), *da.keys()]}.keys()

    definition = EntrypointDef.from_dict(ae | de)

    args = [
        ArgumentDef.from_dict(
            ArgumentDef.merge(aa.get(k, None), da.get(k, None))
        )
        for k in aa.keys()
    ]

    return definition, args


class TermApiError:
    """An error that is raised when a terminal API error occurrs."""
