# <pep8 compliant>

import bpy

from typing import Dict, Tuple

import g3d_exporter.profiler
from g3d_exporter.common import *
from g3d_exporter.profiler import profile


class GShape(object):
    """represents blender 'Shape Keys' panel"""
    def __init__(self, id: str, shape_key: bpy.types.Key):
        self.id: str = id
        self.keys: List[GShapeKey] = []
        self.shape_key: bpy.types.Key = shape_key

        # initialize shape key slots
        for block in shape_key.key_blocks:
            self.keys.append(GShapeKey(block.name, block))

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        root['keys'] = self.keys
        return root


class GShapeKey(object):
    """represents one slot in 'Shape Keys' panel"""

    def __init__(self, name: str, block: bpy.types.ShapeKey):
        self.name = name
        self.block = block
        self.positions: List[float] = list()

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['name'] = self.name
        root['positions'] = self.positions
        return root


class GMeshPart(object):
    def __init__(self, id: str, type: str):
        self.id: str = id
        self.type: str = type
        self.indices: List[int] = []

    def to_dict(self) -> Dict[str, Any]:
        result = dict()
        result['id'] = self.id
        result['type'] = self.type
        result['indices'] = self.indices
        return result


class VertexFlag(object):
    def __init__(self, name: str, length: int):
        self.name: str = name
        self.length: int = length

    @profile
    def __eq__(self, o: object) -> bool:
        return isinstance(o, type(self)) and o.name == self.name and o.length == self.length

    @profile
    def __hash__(self):
        return hash((self.name, self.length))

    def __str__(self):
        return f"{self.name}/{self.length}"


class GMesh(object):
    """
    mesh is unique for attributes flags and for meshes with shapekeys, all other blender meshes will be merged into single mesh
    """
    def __init__(self, attributes: Tuple[VertexFlag]):
        self.attributes: Tuple[VertexFlag] = attributes
        self.vertices: List[float] = list()
        self.parts: List[GMeshPart] = list()

    def vertex_size(self):
        return sum(attr.length for attr in self.attributes)

    def vertex_count(self):
        return int(len(self.vertices) / self.vertex_size())

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['attributes'] = self.attributes
        root['vertices'] = self.vertices
        root['parts'] = self.parts
        return root


class GTexture(object):
    def __init__(self, id: str, type: str, filename: str, image: bpy.types.Image):
        self.id: str = id
        self.type: str = type
        self.filename: str = filename
        self.image: bpy.types.Image = image

    def __str__(self) -> str:
        return f"GTexture({self.id}, {self.type}, {self.filename})"

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        root['filename'] = self.filename
        root['type'] = self.type
        return root


class GMaterial(object):
    def __init__(self, id: str):
        self.id: str = id
        self.attributes: Dict[str, Any] = dict()
        self.textures: List[GTexture] = list()

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        root.update(self.attributes)
        root['textures'] = self.textures
        return root


class BonePart(object):
    """represents bone in node part"""
    def __init__(self, name: str, matrix: Matrix, index: int) -> None:
        self.name = name
        self.matrix: Matrix = matrix
        self.index = index

    def __str__(self) -> str:
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['node'] = self.name
        root['translation'] = conv_vec(self.matrix.to_translation(), 0.0)
        root['rotation'] = conv_quat(self.matrix.to_quaternion())
        root['scale'] = conv_vec(self.matrix.to_scale(), 0.0)
        return root


class GNodePart(object):
    """node part binds mesh part and material"""
    def __init__(self, material: str, meshpart: str):
        self.meshpart = meshpart
        self.material = material
        self.bones: List[BonePart] = list()
        self.uvMapping = [[]]  # TODO what is this for??? -_-

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['meshpartid'] = self.meshpart
        root['materialid'] = self.material
        if self.bones:
            root['bones'] = self.bones
        root['uvMapping'] = self.uvMapping
        return root


class GNode(object):
    """represents blender scene object or armature bones tree"""
    def __init__(self, id: str):
        self.id = id
        self.parts: List[GNodePart] = []
        self.children: List[GNode] = []
        self.parent: GNode = None
        self.scale: Vector = None
        self.translation: Vector = None
        self.rotation: Quaternion = None

    def set_parent(self, parent):
        if parent == self.parent:
            return

        if self.parent:
            self.parent.children.remove(self)

        self.parent = parent

        if self.parent:
            self.parent.children.append(self)

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        root['rotation'] = conv_quat(self.rotation)
        root['scale'] = conv_vec(self.scale)
        root['translation'] = conv_vec(self.translation)
        root['parts'] = self.parts
        if self.children:
            root['children'] = self.children
        return root


class GBoneKeyframe(object):
    def __init__(self, time: float, pose: Matrix):
        """pose - target for GBoneMatrix"""
        self.keytime: float = time
        self.pose: Matrix = pose

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['keytime'] = self.keytime
        root['rotation'] = conv_quat(self.pose.to_quaternion())
        root['translation'] = conv_vec(self.pose.to_translation())
        root['scale'] = conv_vec(self.pose.to_scale())
        return root


class GBoneAnimation(object):
    def __init__(self, bone_id: str):
        self.bone_id: str = bone_id
        self.keyframes: List[GBoneKeyframe] = []

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['boneId'] = self.bone_id
        root['keyframes'] = self.keyframes
        return root


class GAnimation(object):
    def __init__(self, id: str):
        self.id: str = id
        self.bones: List[GBoneAnimation] = []

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        root['bones'] = self.bones
        return root


class G3dModel(object):
    def __init__(self) -> None:
        self.version = [0, 1]
        self.id: str = ""
        self.meshes: List[GMesh] = list()
        self.materials: List[GMaterial] = list()
        self.nodes: List[GNode] = list()
        self.animations: List[GAnimation] = list()
        self.shapes: List[GShape] = list()

    def to_dict(self) -> Dict[str, Any]:
        # note that shapekeys are not part of specification, so they encode separately
        root = dict()
        root['version'] = self.version
        root['id'] = self.id
        root['meshes'] = self.meshes
        root['materials'] = self.materials
        root['nodes'] = self.nodes
        root['animations'] = self.animations
        return root
