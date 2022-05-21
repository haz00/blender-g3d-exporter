# <pep8 compliant>

from pathlib import Path
import struct
import typing
from mathutils import Color, Quaternion, Vector


def unwrapv(v: typing.Union[Vector, Color]) -> list[float]:
    return [v[0], v[1], v[2]]


def flatten(arr: list[any]) -> list[any]:
    return [item for sublist in arr for item in sublist]


def fbits(f: float) -> int:
    return struct.unpack('>l', struct.pack('>f', f))[0]


def hash_vert(vert: list[float]) -> int:
    p = 31
    r = 1
    for f in vert:
        r = p * r + fbits(f)
    return r


def conv_uv(v: list[float], flip: bool = False) -> list[float]:
    return [v[0], 1.0 - v[1] if flip else [1]]


def conv_vec(v: Vector, w: float = None) -> list[float]:
    conv = unwrapv(v)
    if (w != None):
        conv.append(w)
    return conv


def conv_quat(v: typing.Union[list[float], Quaternion]) -> list[float]:
    # blender quaternion is wxyz
    return [v[1], v[2], v[3], v[0]]


def write(file: Path, data: str):
    with open(file, 'w') as f:
        f.write(data)
        print('write success', file.absolute())
