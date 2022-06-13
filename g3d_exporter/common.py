# <pep8 compliant>
import logging
import struct
from pathlib import Path
from typing import Any, Union, List

import bpy
from mathutils import Color, Matrix, Quaternion, Vector

log = logging.getLogger(__name__)


def unwrapv(v: Union[Vector, Color]) -> List[float]:
    return [v[0], v[1], v[2]]


def flatten(arr: List[Any]) -> List[Any]:
    return [item for sublist in arr for item in sublist]


def float_to_int_bits(f: float) -> int:
    return struct.unpack('>l', struct.pack('>f', f))[0]


def int_bits_to_float(b: int) -> float:
    return struct.unpack('>f', struct.pack('>I', b))[0]


def conv_vec(v: Vector, w: float = None) -> List[float]:
    conv = unwrapv(v)
    if w is not None:
        conv.append(w)
    return conv


def conv_quat(v: Union[List[float], Quaternion]) -> List[float]:
    # blender quaternion is wxyz
    return [v[1], v[2], v[3], v[0]]


def new_transorm_matrix(loc: Vector, rot: Quaternion, sca: Vector) -> Matrix:
    mat_rot = rot.to_matrix().to_4x4()

    mat_loc = Matrix.Translation(loc)

    mat_scax = Matrix.Scale(sca[0], 4, (1.0, 0.0, 0.0))
    mat_scay = Matrix.Scale(sca[1], 4, (0.0, 1.0, 0.0))
    mat_scaz = Matrix.Scale(sca[2], 4, (0.0, 0.0, 1.0))
    mat_sca = mat_scax @ mat_scay @ mat_scaz

    return mat_loc @ mat_rot @ mat_sca


def write(data, file: Path, mode='w') -> Path:
    file.parent.mkdir(exist_ok=True)

    with open(file, mode) as f:
        f.write(data)
        log.debug('write %s', file.absolute())
    return file


class G3dError(Exception):
    def __init__(self, message):
        super().__init__(message)
