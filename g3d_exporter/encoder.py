# <pep8 compliant>
import collections
import json
from json.encoder import encode_basestring_ascii, INFINITY
from typing import Sequence

from g3d_exporter import simpleubjson
from g3d_exporter.model import *


def _default_bin_mapper(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif type(obj) == VertexFlag:
        return obj.name
    else:
        raise simpleubjson.exceptions.EncodeError(type(obj))


def encode_binary(g3d: G3dModel) -> Any:
    return simpleubjson.encode(g3d, old_format_json=True, default=_default_bin_mapper)


def encode_json(obj):
    return json.dumps(obj, cls=G3DJsonEncoder)


class G3DJsonEncoder(json.JSONEncoder):
    ln = '\n'
    spaces = ' ' * 2
    key_sep = ': '
    item_sep = ', '
    _encoder = encode_basestring_ascii
    float_format = "%9.6f"

    def iterencode(self, obj: object, _one_shot=False):
        for chunk in self._interencode_object(obj, 0):
            yield chunk

    def _interencode_object(self, obj: object, lvl: int):

        items: Dict[str, object] = obj

        if not isinstance(items, dict):
            items = obj.to_dict()

        yield self._indentln(lvl) + '{'

        content_lvl = lvl + 1
        count = 0

        for key in items:
            value = items[key]

            yield self._indentln(content_lvl)
            yield self._encoder(key)
            yield self.key_sep

            if isinstance(value, str):
                yield self._encoder(value)
            elif isinstance(value, int):
                yield str(value)
            elif isinstance(value, float):
                yield self._floatstr(value)
            elif isinstance(value, collections.abc.Sequence):
                series_break = None

                if isinstance(obj, GMesh) and key == "vertices":
                    series_break = obj.vertex_size()
                elif isinstance(obj, GMeshPart) and key == 'indices':
                    series_break = 12
                elif isinstance(obj, GShapeKey) and key == 'positions':
                    series_break = 3

                for chunk in self._interencode_list(value, content_lvl, series_break):
                    yield chunk
            else:
                raise ValueError(f'unknown type for key value: {key}: {type(value)}')

            count += 1
            if count < len(items):
                yield self.item_sep

        yield self._indentln(lvl) + '}'

    def _interencode_list(self, items: Sequence[Any], lvl: int, series_break: int = None):
        content_lvl = lvl + 1

        yield '[ '

        handle_new_line = len(items) > 4

        if handle_new_line:
            yield self._indentln(content_lvl)

        for i, value in enumerate(items):

            if isinstance(value, str):
                yield self._encoder(value)
            elif isinstance(value, int):
                yield str(value)
            elif isinstance(value, float):
                yield self._floatstr(value)
            elif isinstance(value, VertexFlag):
                yield self._encoder(value.name)
            elif isinstance(value, list):
                for chunk in self._interencode_list(value, content_lvl):
                    yield chunk
            else:
                for chunk in self._interencode_object(value, content_lvl):
                    yield chunk

            if i + 1 < len(items):
                yield self.item_sep

            if series_break is not None and (i + 1) % series_break == 0:
                yield self._indentln(content_lvl)

        if handle_new_line:
            yield self._indentln(lvl)

        yield ' ]'

    def _floatstr(self, o: float) -> str:
        if o != o:
            return 'NaN'
        elif o == INFINITY:
            return 'Infinity'
        elif o == -INFINITY:
            return '-Infinity'
        else:
            return self.float_format % o

    def _indentln(self, lvl: int) -> str:
        return self.ln + self.spaces * lvl