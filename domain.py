# <pep8 compliant>

from utils import conv_quat, conv_vec, flatten, unwrapv
import bpy
import os
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.node_shader_utils import ShaderImageTextureWrapper
from mathutils import Matrix, Quaternion, Vector


class GShape(object):
    """represents blender 'Shape Keys' panel"""

    def __init__(self, id: str, source: bpy.types.Key):
        self.id: str = id
        self.keys: list[GShapeKey] = []
        self.source: bpy.types.Key = source

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['id'] = self.id
        root['keys'] = self.keys
        return root


class GShapeKey(object):
    """represents one slot in 'Shape Keys' panel"""

    def __init__(self, name: str, source):
        self.name = name
        self.source = source
        self.positions: list[list[float]] = []

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['name'] = self.name
        root['positions'] = flatten(self.positions)
        return root


class GMeshPart(object):
    def __init__(self, id: str, type: str):
        self.id: str = id
        self.type: str = type
        self.indices: list[int] = []

    def to_dict(self) -> dict[str, any]:
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
    mesh is unique for attributes flags and for object with shapekeys, all other blender meshes will be merged into single mesh
    """

    def __init__(self, attributes: list[GVertexAttribute], id: str = None):
        self.attributes: list[GVertexAttribute] = attributes
        self.vertices: list[list[float]] = []
        self.vertex_index: dict[int, int] = {}  # vertex hash -> vertex index
        self.parts: list[GMeshPart] = []
        self.id: bool = id

    def get_mesh_part(self, name: str):
        for p in self.parts:
            if (p.id == name):
                return p
        return None

    def vertex_size(self):
        return sum(attr.length for attr in self.attributes)

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['attributes'] = self.attributes
        root['vertices'] = flatten(self.vertices)
        root['parts'] = self.parts
        return root


class GTexture(object):
    def __init__(self, id: str, type: str, filename: str):
        self.id: str = id
        self.type: str = type
        self.filename: str = filename

    def __str__(self) -> str:
        return f"GTexture({self.id}, {self.type}, {self.filename})"

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['id'] = self.id
        root['filename'] = self.filename
        root['type'] = self.type
        return root


class GMaterial(object):
    """uses active output and connected Principled BSDF node sockets to collect infomation"""

    def __init__(self, id: str, index: int):
        self.id: str = id
        self.index = index
        self.diffuse: list[float] = None
        self.ambient: list[float] = None
        self.emissive: list[float] = None
        self.specular: list[float] = None
        self.reflection: list[float] = None
        self.opacity: float = None
        self.shininess: float = None
        self.textures: list[GTexture] = []

    def setup_principled(self, bsdf: PrincipledBSDFWrapper):
        if (not self.setup_texture('TRANSPARENCY', bsdf.alpha_texture)):
            self.opacity = bsdf.alpha

        if (not self.setup_texture('DIFFUSE', bsdf.base_color_texture)):
            self.diffuse = unwrapv(bsdf.base_color)

        if (not self.setup_texture('EMISSIVE', bsdf.emission_color_texture)):
            self.emissive = unwrapv(bsdf.emission_color)

        if (not self.setup_texture('SHININESS', bsdf.roughness_texture)):
            self.shininess = 1.0 - bsdf.roughness

        if (not self.setup_texture('SPECULAR', bsdf.specular_texture)):
            self.specular = [bsdf.specular, bsdf.specular, bsdf.specular]

        if (not self.setup_texture('REFLECTION', bsdf.metallic_texture)):
            self.reflection = [bsdf.metallic, bsdf.metallic, bsdf.metallic]

        self.setup_texture('NORMAL', bsdf.normalmap_texture)

        # TODO also look for nodes
        if (not bpy.context.scene.world.use_nodes):
            self.ambient = unwrapv(bpy.context.scene.world.color)

    def setup_texture(self, type: str, wrapper: ShaderImageTextureWrapper) -> bool:
        if (wrapper and wrapper.image):
            filename = os.path.basename(wrapper.image.filepath_from_user())
            tex = GTexture(wrapper.image.name, type, filename)
            self.textures.append(tex)
            print(f"add texture {tex}")
            return True
        return False

    def to_dict(self) -> dict[str, any]:
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

    def __init__(self, node: str, index: int, matrix: Matrix):
        self.node: str = node
        self.matrix: Matrix = matrix
        self.index: int = index

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['node'] = self.node
        root['translation'] = conv_vec(self.matrix.to_translation(), 0.0)
        root['rotation'] = conv_quat(self.matrix.to_quaternion())
        root['scale'] = conv_vec(self.matrix.to_scale(), 0.0)
        return root


class GNodePart(object):
    """node part binds mesh part and material"""

    def __init__(self, materialid: str, meshpartid: str):
        self.meshpartid: str = meshpartid
        self.materialid: str = materialid
        self.bones: list[GBoneMatrix] = []
        self.uvMapping = [[]]  # TODO what is this for???

    def get_bone(self, name: str) -> GBoneMatrix:
        for b in self.bones:
            if (b.node == name):
                return b
        return None

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['meshpartid'] = self.meshpartid
        root['materialid'] = self.materialid
        if (len(self.bones) > 0):
            root['bones'] = self.bones
        root['uvMapping'] = self.uvMapping
        return root


class GNode(object):
    """represents blender scene object or armamature bones tree"""

    def __init__(self, id: str, source: bpy.types.Object):
        """
        source - original blender object, can be None if node is armature bone
        """
        self.id = id
        self.parts: list[GNodePart] = []
        self.children: list[GNode] = []
        self.source: bpy.types.Object = source
        self.parent: GNode = None

        mat: Matrix = source.matrix_world if (source) else Matrix.Identity(4)

        if (source and source.parent):
            mat = source.parent.matrix_world.inverted() @ mat

        (t, r, s) = mat.decompose()

        self.scale: Vector = s
        self.translation: Vector = t
        self.rotation: Quaternion = r

    def to_dict(self) -> dict[str, any]:
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

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['keytime'] = self.keytime
        root['rotation'] = conv_quat(self.pose.to_quaternion())
        root['translation'] = conv_vec(self.pose.to_translation())
        root['scale'] = conv_vec(self.pose.to_scale())
        return root


class GBoneAnimation(object):
    def __init__(self, bone_id: str):
        self.bone_id: str = bone_id
        self.keyframes: list[GBoneKeyframe] = []

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['boneId'] = self.bone_id
        root['keyframes'] = self.keyframes
        return root


class GAnimation(object):
    def __init__(self, id: str):
        self.id: str = id
        self.bones: list[GBoneAnimation] = []

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['id'] = self.id
        root['bones'] = self.bones
        return root


class G3D(object):
    def __init__(self) -> None:
        self.version = [0, 1]
        self.id: str = ""
        self.meshes: list[GMesh] = []
        self.materials: list[GMaterial] = []
        self.nodes: list[GNode] = []
        self.animations: list[GAnimation] = []
        self.shapes: list[GShape] = []

    def add_mesh(self, mesh: GMesh):
        self.meshes.append(mesh)
        print(f'add mesh: {len(self.meshes)}')

    def get_mesh(self, attr: list[GVertexAttribute], id: str = None) -> GMesh:
        for m in self.meshes:
            if (m.id == id and m.attributes == attr):
                return m
        return None

    def get_material(self, id: str) -> GMaterial:
        for e in self.materials:
            if (e.id == id):
                return e
        return None

    def to_dict(self) -> dict[str, any]:
        root = dict()
        root['version'] = self.version
        root['id'] = self.id
        root['meshes'] = self.meshes
        root['materials'] = self.materials
        root['nodes'] = self.nodes
        root['animations'] = self.animations
        # shapekeys encodes separetly
        return root
