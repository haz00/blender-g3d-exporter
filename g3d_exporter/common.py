# <pep8 compliant>
import logging
import struct
from pathlib import Path
from typing import Any, Union, List

from mathutils import Color, Matrix, Quaternion, Vector

from g3d_exporter.profiler import profile

log = logging.getLogger(__name__)

pack_float = struct.Struct('>f').pack
pack_uint = struct.Struct('>I').pack
unpack_float = struct.Struct('>f').unpack
unpack_long = struct.Struct('>l').unpack


def unwrapv(v: Union[Vector, Color]) -> List[float]:
    return [v[0], v[1], v[2]]


@profile
def flatten(arr: List[Any]) -> List[Any]:
    return [item for sublist in arr for item in sublist]


@profile
def float_to_int_bits(f: float) -> int:
    return unpack_long(pack_float(f))[0]


@profile
def int_bits_to_float(b: int) -> float:
    return unpack_float(pack_uint(b))[0]


def conv_vec(v: Vector, w: float = None) -> List[float]:
    conv = unwrapv(v)
    if w is not None:
        conv.append(w)
    return conv


def conv_quat(v: Union[List[float], Quaternion]) -> List[float]:
    # blender quaternion is wxyz
    return [v[1], v[2], v[3], v[0]]


@profile
def new_transorm_matrix(loc: Vector, rot: Quaternion, sca: Vector) -> Matrix:
    mat_rot = rot.to_matrix().to_4x4()

    mat_loc = Matrix.Translation(loc)

    mat_scax = Matrix.Scale(sca[0], 4, (1.0, 0.0, 0.0))
    mat_scay = Matrix.Scale(sca[1], 4, (0.0, 1.0, 0.0))
    mat_scaz = Matrix.Scale(sca[2], 4, (0.0, 0.0, 1.0))
    mat_sca = mat_scax @ mat_scay @ mat_scaz

    return mat_loc @ mat_rot @ mat_sca


@profile
def write(data, file: Path, mode='w') -> Path:
    file.parent.mkdir(exist_ok=True)

    with open(file, mode) as f:
        f.write(data)
        log.debug('write %s', file.absolute())
    return file


class G3dError(Exception):
    def __init__(self, message):
        super().__init__(message)
