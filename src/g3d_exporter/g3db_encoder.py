# <pep8 compliant>

from typing import Any, Tuple, Union, List

from . import simpleubjson
from .model import *


def _default_mapper(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif isinstance(obj, GVertexAttribute):
        return obj.name
    else:
        raise simpleubjson.exceptions.EncodeError(type(obj))


def encode(g3d: G3dModel) -> Any:
    return simpleubjson.encode(g3d, old_format_json=True, default=_default_mapper)