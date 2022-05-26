# <pep8 compliant>

import json
from json.encoder import encode_basestring_ascii, INFINITY
from typing import Any, Tuple, Union, List

from domain import *

ln = '\n'
spaces = ' ' * 2
key_sep = ': '
item_sep = ', '
_encoder = encode_basestring_ascii
float_format = "%9.6f"


class G3DJsonEncoder(json.JSONEncoder):

    def iterencode(self, obj: object, _one_shot=False):
        for chunk in self._interncode_object(obj, 0):
            yield chunk

    def _interncode_object(self, obj: object, lvl: int):

        items: Dict[str, object] = obj

        if (not isinstance(obj, dict)):
            items = obj.to_dict()

        yield _indentln(lvl) + '{'

        content_lvl = lvl + 1
        count = 0

        for key in items:
            value = items[key]

            yield _indentln(content_lvl)
            yield _encoder(key)
            yield key_sep

            if (isinstance(value, str)):
                yield _encoder(value)
            elif (isinstance(value, int)):
                yield str(value)
            elif (isinstance(value, float)):
                yield _floatstr(value)
            elif (isinstance(value, list)):
                series_break = None

                if (isinstance(obj, GMesh) and key == "vertices"):
                    series_break = obj.vertex_size()
                elif (isinstance(obj, GMeshPart) and key == 'indices'):
                    series_break = 12
                elif (isinstance(obj, GShapeKey) and key == 'positions'):
                    series_break = 3

                for chunk in self._interncode_list(value, content_lvl, series_break):
                    yield chunk
            else:
                raise ValueError(
                    f'unknown type for key value: {key}: {type(value)}')

            count += 1
            if (count < len(items)):
                yield item_sep

        yield _indentln(lvl) + '}'

    def _interncode_list(self, items: List[Any], lvl: int, series_break: int = None):
        content_lvl = lvl + 1

        yield '[ '

        handle_new_line = len(items) > 4

        if (handle_new_line):
            yield _indentln(content_lvl)

        for i, value in enumerate(items):

            if (isinstance(value, str)):
                yield _encoder(value)
            elif (isinstance(value, int)):
                yield str(value)
            elif (isinstance(value, float)):
                yield _floatstr(value)
            elif (isinstance(value, GVertexAttribute)):
                yield _encoder(value.name)
            elif (isinstance(value, list)):
                for chunk in self._interncode_list(value, content_lvl):
                    yield chunk
            else:
                for chunk in self._interncode_object(value, content_lvl):
                    yield chunk

            if (i + 1 < len(items)):
                yield item_sep

            if (series_break != None and (i + 1) % series_break == 0):
                yield _indentln(content_lvl)

        if (handle_new_line):
            yield _indentln(lvl)

        yield ' ]'


def _floatstr(o: float) -> str:
    if o != o:
        return 'NaN'
    elif o == INFINITY:
        return 'Infinity'
    elif o == -INFINITY:
        return '-Infinity'
    else:
        return float_format % o


def _indentln(lvl: int) -> str:
    return ln + spaces * lvl
