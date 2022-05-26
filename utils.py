# <pep8 compliant>

from pathlib import Path
import struct
from typing import Any, Union, List
from mathutils import Color, Quaternion, Vector


def unwrapv(v: Union[Vector, Color]) -> List[float]:
    return [v[0], v[1], v[2]]


def flatten(arr: List[Any]) -> List[Any]:
    return [item for sublist in arr for item in sublist]


def float_to_int_bits(f: float) -> int:
    return struct.unpack('>l', struct.pack('>f', f))[0]


def int_bits_to_float(b: int) -> float:
    return struct.unpack('>f', struct.pack('>I', b))[0]


def hash_vert(vert: List[float]) -> int:
    p = 31
    r = 1
    for f in vert:
        r = p * r + float_to_int_bits(f)
    return r


def conv_uv(v: List[float], flip: bool = False) -> List[float]:
    return [v[0], 1.0 - v[1] if flip else [1]]


def conv_vec(v: Vector, w: float = None) -> List[float]:
    conv = unwrapv(v)
    if (w != None):
        conv.append(w)
    return conv


def conv_quat(v: Union[List[float], Quaternion]) -> List[float]:
    # blender quaternion is wxyz
    return [v[1], v[2], v[3], v[0]]


def pack_color(rgba: List[float]) -> float:
    abgr_int = int(rgba[3] * 255) << 24 | int(rgba[2] * 255) << 16 | int(rgba[1] * 255) << 8 | int(rgba[0] * 255)
    return int_bits_to_float(abgr_int & 0xfeffffff)


def write(file: Path, data: str):
    with open(file, 'w') as f:
        f.write(data)
        print('write success', file.absolute())
