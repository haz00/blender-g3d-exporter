# <pep8 compliant>

import collections
import bpy
from mathutils import Matrix, Quaternion, Vector

from typing import Any, Dict, Iterable, List, OrderedDict, Set, Iterable

from .common import *


class GShape(object):
    """represents blender 'Shape Keys' panel"""

    def __init__(self, id: str, source: bpy.types.Key):
        self.id: str = id
        self.keys: List[GShapeKey] = []
        self.source: bpy.types.Key = source

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        root['keys'] = self.keys
        return root


class GShapeKey(object):
    """represents one slot in 'Shape Keys' panel"""

    def __init__(self, name: str, source):
        self.name = name
        self.source = source
        self.positions: List[List[float]] = []

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['name'] = self.name
        root['positions'] = flatten(self.positions)
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


class GVertexAttribute(object):
    def __init__(self, name: str, length: int):
        self.name: str = name
        self.length: int = length

    def __eq__(self, o: object) -> bool:
        return isinstance(o, type(self)) and o.name == self.name and o.length == self.length


class GMesh(object):
    """
    mesh is unique for attributes flags and for meshes with shapekeys, all other blender meshes will be merged into single mesh
    """

    def __init__(self, attributes: List[GVertexAttribute], id: str = None):
        self.attributes: List[GVertexAttribute] = attributes
        self.vertices: List[List[float]] = list()
        self.vertex_index: Dict[int, int] = dict()  # vertex hash -> vertex index
        self.parts: OrderedDict[str, GMeshPart] = collections.OrderedDict()
        self.id: bool = id


    def add_part(self, part: GMeshPart) -> GMeshPart:
        self.parts[part.id] = part
        return part


    def get_meshpart(self, id: str):
        return self.parts.get(id, None)


    def vertex_size(self):
        return sum(attr.length for attr in self.attributes)


    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['attributes'] = self.attributes
        root['vertices'] = flatten(self.vertices)
        root['parts'] = list(self.parts.values())
        return root


class GTexture(object):
    def __init__(self, id: str, type: str, filename: str, source: bpy.types.Image):
        self.id: str = id
        self.type: str = type
        self.filename: str = filename
        self.source: bpy.types.Image = source

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
        self.diffuse: List[float] = None
        self.ambient: List[float] = None
        self.emissive: List[float] = None
        self.specular: List[float] = None
        self.reflection: List[float] = None
        self.opacity: float = None
        self.shininess: float = None
        self.textures: List[GTexture] = []

    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        if(self.diffuse != None):
            root['diffuse'] = self.diffuse
        if(self.ambient != None):
            root['ambient'] = self.ambient
        if(self.emissive != None):
            root['emissive'] = self.emissive
        if(self.specular != None):
            root['specular'] = self.specular
        if(self.opacity != None):
            root['opacity'] = self.opacity
        if(self.shininess != None):
            root['shininess'] = self.shininess
        if(self.reflection):
            root['reflection'] = self.reflection
        root['textures'] = self.textures
        return root


class GBoneMatrix(object):
    """represents node part bone"""

    def __init__(self, id: str, matrix: Matrix):
        self.id: str = id
        self.matrix: Matrix = matrix
        self.index: int = None


    def __str__(self) -> str:
        return self.id


    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['node'] = self.id
        root['translation'] = conv_vec(self.matrix.to_translation(), 0.0)
        root['rotation'] = conv_quat(self.matrix.to_quaternion())
        root['scale'] = conv_vec(self.matrix.to_scale(), 0.0)
        return root


class GNodePart(object):
    """node part binds mesh part and material"""

    def __init__(self, material: GMaterial, meshpart: GMeshPart):
        self.meshpart = meshpart
        self.material = material
        self.bones: OrderedDict[str, GBoneMatrix] = collections.OrderedDict()
        self.uvMapping = [[]]  # TODO what is this for???


    def add_bone(self, bone: GBoneMatrix) -> GBoneMatrix:
        bone.index = len(self.bones)
        self.bones[bone.id] = bone


    def get_bone(self, id: str) -> GBoneMatrix:
        return self.bones.get(id, None)


    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['meshpartid'] = self.meshpart.id
        root['materialid'] = self.material.id
        if (len(self.bones) > 0):
            root['bones'] = list(self.bones.values())
        root['uvMapping'] = self.uvMapping
        return root


class GNode(object):
    """represents blender scene object or armamature bones tree"""

    def __init__(self, id: str, source: bpy.types.Object):
        """
        source - original blender object, can be None if node is armature bone
        """
        self.id = id
        self.parts: List[GNodePart] = []
        self.children: List[GNode] = []
        self.source: bpy.types.Object = source
        self.parent: GNode = None

        mat: Matrix = source.matrix_world if (source) else Matrix.Identity(4)

        if (source and source.parent):
            mat = source.parent.matrix_world.inverted() @ mat

        (t, r, s) = mat.decompose()

        self.scale: Vector = s
        self.translation: Vector = t
        self.rotation: Quaternion = r


    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['id'] = self.id
        root['rotation'] = conv_quat(self.rotation)
        root['scale'] = conv_vec(self.scale)
        root['translation'] = conv_vec(self.translation)
        root['parts'] = self.parts
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
        self.meshes: List[GMesh] = []
        self.materials: Dict[str, GMaterial] = dict()
        self.nodes: List[GNode] = []
        self.animations: List[GAnimation] = []
        self.shapes: List[GShape] = []

    def add_mesh(self, mesh: GMesh):
        self.meshes.append(mesh)
        print(f'add mesh: {len(self.meshes)}')


    def get_mesh(self, attr: List[GVertexAttribute], id: str, has_shape: bool) -> GMesh:
        for m in self.meshes:
            if (has_shape and m.id == id) or (not has_shape and m.attributes == attr):
                return m
        return None


    def get_material(self, id: str) -> GMaterial:
        return self.materials.get(id, None)


    def to_dict(self) -> Dict[str, Any]:
        root = dict()
        root['version'] = self.version
        root['id'] = self.id
        root['meshes'] = self.meshes
        root['materials'] = list(self.materials.values())
        root['nodes'] = self.nodes
        root['animations'] = self.animations
        # shapekeys encodes separetly
        return root


class G3dError(Exception):
    def __init__(self, message):
        super().__init__(message)
        