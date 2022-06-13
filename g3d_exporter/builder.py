# <pep8 compliant>
import collections
import logging

import bmesh
import typing
import bpy

from mathutils import Euler
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.node_shader_utils import ShaderImageTextureWrapper

from typing import Tuple, Set, Dict
import os

from g3d_exporter import model
from g3d_exporter.common import *

log = logging.getLogger(__name__)


class ModelOptions(object):
    def __init__(self) -> None:
        self.y_up = True
        self.selected_only = False
        self.use_normal = True
        self.use_color = True
        self.use_material = True
        self.packed_color = True
        self.use_uv = True
        self.use_tangent = True
        self.use_binormal = True
        self.flip_uv = True
        self.use_armature = True
        self.bones_per_vertex = 4
        self.max_bones_per_nodepart = 12
        self.max_vertices_per_mesh = 32767
        self.use_shapekeys = True
        self.use_actions = True
        self.add_bone_tip = True
        self.apply_modifiers = True
        self.fps = bpy.context.scene.render.fps
        self.primitive_type = 'TRIANGLES'


def build(opt: ModelOptions) -> model.G3dModel:
    return G3Builder(opt).build()


class G3MeshData(object):
    def __init__(self, attributes: Tuple[model.VertexFlag]) -> None:
        self.attributes = attributes
        self.vertices: List[Vertex] = list()
        self.vertex_index: Dict[Vertex, int] = dict()
        self.parts: Dict[str, MeshpartData] = dict()
        self.shape: model.GShape = None

    def __str__(self):
        return ", ".join([str(a) for a in self.attributes])


class MeshpartData(object):
    def __init__(self, id: str, primitive_type: str, meshdata: G3MeshData) -> None:
        self.id = id
        self.meshdata = meshdata
        self.primitive_type = primitive_type
        self.indices: List[int] = list()


class TextureBuilder(object):
    def __init__(self, opt: ModelOptions) -> None:
        self.opt = opt

    def build(self, image: bpy.types.Image, type: str) -> model.GTexture:
        filename = os.path.basename(image.filepath_from_user())
        id = f"{image.name}_{type}"
        return model.GTexture(id, type, filename, image)


class G3Data(object):
    def __init__(self):
        self.animations: Dict[str, model.GAnimation] = dict()
        self.materials: Dict[str, model.GMaterial] = dict()
        self.meshes: Dict[int, G3MeshData] = dict()
        self.mesh_node_data: Dict[int, MeshNodeData] = dict()
        self.nodes: List[model.GNode] = list()


class MaterialBuilder(object):
    def __init__(self, g3data: G3Data, opt: ModelOptions) -> None:
        self.opt = opt
        self.g3data = g3data
        self.texture_builder = TextureBuilder(opt)

    def build(self, material: bpy.types.Material) -> model.GMaterial:
        gmat = model.GMaterial(material.name)

        if self.opt.use_material:
            if material.use_nodes:
                bsdf = PrincipledBSDFWrapper(material, is_readonly=True)
                self._setup_principled(gmat, bsdf)
            else:
                log.warning("material has no nodes: %s", material.name)

        return gmat

    def _setup_principled(self, mat: model.GMaterial, bsdf: PrincipledBSDFWrapper):
        """Uses active shader output and connected Principled BSDF node sockets to collect information"""
        textures: Dict[str, model.GTexture] = dict()

        if not self._setup_texture(textures, 'TRANSPARENCY', bsdf.alpha_texture):
            mat.attributes['opacity'] = bsdf.alpha

        if not self._setup_texture(textures, 'DIFFUSE', bsdf.base_color_texture):
            mat.attributes['diffuse'] = unwrapv(bsdf.base_color)

        if not self._setup_texture(textures, 'EMISSIVE', bsdf.emission_color_texture):
            mat.attributes['emissive'] = unwrapv(bsdf.emission_color)

        if not self._setup_texture(textures, 'SHININESS', bsdf.roughness_texture):
            mat.attributes['shininess'] = 1.0 - bsdf.roughness

        if not self._setup_texture(textures, 'SPECULAR', bsdf.specular_texture):
            mat.attributes['specular'] = [bsdf.specular, bsdf.specular, bsdf.specular]

        if not self._setup_texture(textures, 'REFLECTION', bsdf.metallic_texture):
            mat.attributes['reflection'] = [bsdf.metallic, bsdf.metallic, bsdf.metallic]

        self._setup_texture(textures, 'NORMAL', bsdf.normalmap_texture)

        # TODO also look for nodes
        if not bpy.context.scene.world.use_nodes:
            mat.attributes['ambient'] = unwrapv(bpy.context.scene.world.color)

        mat.textures = list(textures.values())

    def _setup_texture(self, textures: Dict[str, model.GTexture], type: str,
                       wrapper: ShaderImageTextureWrapper) -> bool:
        if wrapper and wrapper.image and wrapper.image.source == 'FILE':
            tex = self.texture_builder.build(wrapper.image, type)
            textures[tex.id] = tex
            return True
        return False


class Vertex(object):
    def __init__(self, original: bpy.types.MeshVertex, data: Tuple[float] = ()):
        self.data: Tuple[float] = data
        self.hash: int = -1
        self.original = original

    def __str__(self):
        return str(self.data)

    def __hash__(self):
        if self.hash == -1:
            self.hash = 1
            for f in self.data:
                self.hash = 31 * self.hash + float_to_int_bits(f)
        return self.hash

    def __eq__(self, other):
        return isinstance(other, type(self)) and hash(self) == hash(other)


class NodePartBuilder(object):
    def __init__(self, material: model.GMaterial, meshpart: MeshpartData) -> None:
        self.material = material
        self.meshpart = meshpart
        self.bones: typing.OrderedDict[str, model.BonePart] = collections.OrderedDict()

    def get_bonepart(self, bone: bpy.types.Bone) -> model.BonePart:
        """get or create bonepart"""
        bonepart = self.bones.get(bone.name, None)

        if not bonepart:
            bonepart = model.BonePart(bone.name, bone.matrix_local, len(self.bones))
            self.bones[bone.name] = bonepart

        return bonepart

    def count_bone(self, bones: Dict[str, bpy.types.Bone]) -> int:
        if not self.bones or not bones:
            return 0

        matches = 0
        for name in bones:
            if name in self.bones:
                matches += 1
        return matches

    def build(self) -> model.GNodePart:
        part = model.GNodePart(self.material.id, self.meshpart.id)
        part.bones = list(self.bones.values())
        return part


class MeshMetaInfo(object):
    def __init__(self, obj: bpy.types.Object, mesh: bpy.types.Mesh, armature: bpy.types.Object):
        self.obj = obj
        self.mesh = mesh
        self.armature = armature
        self.attributes: List[AttributeBuilder] = list()
        self.shape: model.GShape = None

    def flags(self) -> Tuple[model.VertexFlag]:
        return tuple(flatten([b.flags() for b in self.attributes]))


class VertexBoneGroup:
    def __init__(self, bone: bpy.types.Bone, group: bpy.types.VertexGroupElement):
        self.bone = bone
        self.group = group
        self.weight = group.weight
        self.index: int = None  # index of bone element in nodepart


class VertexInfo(object):
    def __init__(self, vert: bpy.types.MeshVertex,
                 loop: bpy.types.MeshLoop,
                 obj: bpy.types.Object,
                 mesh: bpy.types.Mesh,
                 opt: ModelOptions) -> None:
        self.vert = vert
        self.loop = loop
        self.obj = obj
        self.mesh = mesh
        self.opt = opt
        """Used to determine the nodepart by bunch of face bones"""
        self.bones: Dict[str, VertexBoneGroup] = None

    def __hash__(self):
        return hash(self.vert)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.vert == other.vert

    def __str__(self):
        return f"VertexInfo: {self.vert.co}; {[b.bone.name for b in self.bones.values()]}"

    def norm_weights(self):
        total = sum(b.weight for _, b in self.bones.items())

        for _, b in self.bones.items():
            b.weight = b.weight / total if (total > 0) else 0


class FaceInfo(object):
    def __init__(self, polygon: bpy.types.MeshPolygon, material: model.GMaterial, opt: ModelOptions) -> None:
        self.polygon = polygon
        self.opt = opt
        self.vertices: List[VertexInfo] = list()
        self.material = material

    def setup(self, meta: MeshMetaInfo):
        """creates vertex builders"""
        for attr in meta.attributes:
            attr.begin_face()

        for iv in range(len(self.polygon.vertices)):
            vert_idx = self.polygon.vertices[iv]
            loop_idx = self.polygon.loop_start + iv

            vert: bpy.types.MeshVertex = meta.mesh.vertices[vert_idx]
            loop: bpy.types.MeshLoop = meta.mesh.loops[loop_idx]

            info = VertexInfo(vert, loop, meta.obj, meta.mesh, self.opt)

            for attr in meta.attributes:
                attr.setup_vertex(info)

            self.vertices.append(info)

    def build(self, meta: MeshMetaInfo, nodepart: NodePartBuilder) -> typing.Generator[Vertex, None, None]:
        """produces vertices"""
        for v_info in self.vertices:

            data: List[float] = list()
            for attr in meta.attributes:
                attr.build(v_info, data, nodepart)

            yield Vertex(v_info.vert, tuple(data))


class AttributeBuilder(object):
    """Vertex attribute of single mesh"""
    def flags(self) -> List[model.VertexFlag]:
        raise ValueError("not implemented")

    def begin_face(self):
        """stage 0: begin face"""
        pass

    def setup_vertex(self, info: VertexInfo):
        """stage 1: setup face vertices"""
        pass

    def filter_nodepart(self, part: NodePartBuilder) -> bool:
        """stage 2: determine nodepart"""
        return True

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        """stage 3: build vertex"""
        raise ValueError("not implemented")


class PositionAttributeBuilder(AttributeBuilder):
    def flags(self):
        return [model.VertexFlag("POSITION", 3)]

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        data.extend(info.vert.co)


class NormalAttributeBuilder(AttributeBuilder):
    def flags(self):
        return [model.VertexFlag("NORMAL", 3)]

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        data.extend(info.vert.normal)


class TangentAttributeBuilder(AttributeBuilder):
    def flags(self):
        return [model.VertexFlag("TANGENT", 3)]

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        data.extend(info.loop.tangent)


class BiTangentAttributeBuilder(AttributeBuilder):
    def flags(self):
        return [model.VertexFlag("BINORMAL", 3)]

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        data.extend(info.loop.bitangent)


class ColorAttributeBuilder(AttributeBuilder):
    def flags(self):
        return [model.VertexFlag("COLOR", 4)]

    def __init__(self, layers: List[bpy.types.MeshLoopColorLayer]):
        """uses active render slot"""
        self.layer = next(filter(lambda layer: layer.active_render, layers))

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        # TODO multiple colors
        data.extend(self.layer.data[info.loop.index].color)  # rgba


class PackedColorAttributeBuilder(ColorAttributeBuilder):
    def flags(self):
        return [model.VertexFlag("COLORPACKED", 1)]

    def __init__(self, layers: List[bpy.types.MeshLoopColorLayer]):
        super().__init__(layers)

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        color = self.layer.data[info.loop.index].color
        data.append(self.pack(color))

    def pack(self, rgba: List[float]) -> float:
        abgr_int = int(rgba[3] * 255) << 24 | int(rgba[2] * 255) << 16 | int(rgba[1] * 255) << 8 | int(rgba[0] * 255)
        return int_bits_to_float(abgr_int & 0xfeffffff)


class UvAttributeBuilder(AttributeBuilder):
    def flags(self):
        return [model.VertexFlag("TEXCOORD0", 2)]

    def __init__(self, layers: List[bpy.types.MeshUVLoopLayer], flip: bool):
        """uses active render slot"""
        self.layer = next(filter(lambda layer: layer.active_render, layers))
        self.flip = flip

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        # TODO multiple uv
        uv = self.layer.data[info.loop.index].uv  # immutable
        data.append(uv[0])
        data.append(1.0 - uv[1] if self.flip else uv[1])


class BlendweightAttributeBuilder(AttributeBuilder):
    def __init__(self,
                 slots: Dict[str, bpy.types.VertexGroup],
                 armature_bones: Dict[str, bpy.types.Bone],
                 length: int,
                 max_bones_per_nodepart: int):
        self.length = length
        self.max_bones_per_nodepart = max_bones_per_nodepart
        self.slots = slots
        self.armature_bones = armature_bones
        self._empty = (0.0, 0.0)
        self._bones: Dict[str, bpy.types.Bone] = dict()

    def flags(self):
        return [model.VertexFlag(f"BLENDWEIGHT{i}", 2) for i in range(self.length)]

    def begin_face(self):
        self._bones.clear()

    def setup_vertex(self, info: VertexInfo):
        """search bone weight by each group assigned to the vertex"""
        info.bones = dict()

        for group_element in info.vert.groups:
            # skip zero weights
            if len(info.bones) == self.length:
                break

            armature_bone = self._get_valid_bone(group_element)

            if armature_bone:
                group = VertexBoneGroup(armature_bone, group_element)
                info.bones[armature_bone.name] = group

                # Cache to know which unique bones are using by this face.
                # Used to fast determine the nodepart by bunch of bones,
                # where this face will be placed
                self._bones[armature_bone.name] = group.bone

        info.norm_weights()

    def _get_valid_bone(self, group_element: bpy.types.VertexGroupElement) -> bpy.types.Bone:
        if group_element.weight <= 0:
            return None

        group_idx = group_element.group
        group_name = self.slots[group_idx].name

        # ensures that the group is real bone
        return self.armature_bones.get(group_name, None)

    def filter_nodepart(self, part: NodePartBuilder) -> bool:
        """here we need to find a part which can supply all bones of this face"""
        if not self._bones:
            return True

        # make sure that the all bones from blendweights are present in part's bones
        matches_count = part.count_bone(self._bones)
        rest_count = len(self._bones) - matches_count

        # true - if there are enough space for the rest of vertex bones,
        # false - to create a new nodepart
        if len(part.bones) + rest_count <= self.max_bones_per_nodepart:
            return True
        return False

    def build(self, info: VertexInfo, data: List[float], nodepart: NodePartBuilder):
        # add vertex bones to nodepart and update bone index
        has_blendweights = False

        for bone_group in info.bones.values():
            has_blendweights = has_blendweights or bone_group.weight > 0

            bonepart = nodepart.get_bonepart(bone_group.bone)
            bone_group.index = bonepart.index

            data.append(float(bone_group.index))
            data.append(bone_group.weight)

        if not has_blendweights:
            raise G3dError(f"Vertex {info.vert.co} has no any weights in mesh: {info.mesh.name}. "
                           f"Try to 'Clean Vertex Group Weights' or increase 'Bones per vertex' option")

        if len(nodepart.bones) > self.max_bones_per_nodepart:
            # in some cases when option was configured incorrectly
            raise G3dError(f"Bones per node part: {len(nodepart.bones)} > {self.max_bones_per_nodepart} max. "
                           f"Check 'Nodepart Bones' option")

        # fill the gaps if there are no bones assigned
        for i in range(len(info.bones), self.length):
            data.extend(self._empty)

    def set_optimal_length(self, mesh: bpy.types.Mesh, limit: int):
        """find the max groups count assigned to any vertex to make optimal count of blendweights"""
        self.length = 0
        groups: Set[str] = set()

        for v in mesh.vertices:
            for group_element in v.groups:
                bone = self._get_valid_bone(group_element)
                if not bone:
                    continue

                groups.add(bone.name)
                self.length = min(len(groups), limit)

                if self.length == limit:
                    return


class MeshNodeData(object):
    """Holds data that can be used for multiple nodes"""
    def __init__(self):
        self.parts: List[NodePartBuilder] = list()


class MeshNodeDataBuilder(object):
    def __init__(self, g3data: G3Data, opt: ModelOptions) -> None:
        self.g3data = g3data
        self.opt = opt
        self.material_builder = MaterialBuilder(g3data, opt)

    def build(self, obj: bpy.types.Object,
              mesh: bpy.types.Mesh,
              armature: bpy.types.Object) -> Union[MeshNodeData, None]:
        log.debug('setup object %s, mesh %s', obj.name, obj.data.name)

        if not len(obj.material_slots):
            log.warning('%s has no materials', obj.name)
            return None

        if not len(mesh.polygons):
            log.warning("mesh is empty %s", mesh.name)
            return None

        meta = self._analyze_mesh(obj, mesh, armature)
        g3mesh = self._get_g3mesh(meta)
        return self._convert(meta, g3mesh)

    def _convert(self, meta: MeshMetaInfo, g3mesh: G3MeshData) -> MeshNodeData:
        """converts blender mesh to g3d mesh"""
        meshdata = MeshNodeData()
        mesh = meta.mesh
        obj = meta.obj

        for polygon in mesh.polygons:

            matslot = obj.material_slots[polygon.material_index]
            material = self._get_material(matslot.material)

            face = FaceInfo(polygon, material, self.opt)
            face.setup(meta)

            nodepart = self._get_nodepart(meta, material, g3mesh, meshdata.parts)

            for vert in face.build(meta, nodepart):
                self._add_vertex(vert, g3mesh, nodepart.meshpart)

        self._check_mesh_limits(g3mesh)
        return meshdata

    def _add_vertex(self, vert: Vertex, g3mesh: G3MeshData, meshpart: MeshpartData):
        vert_index = g3mesh.vertex_index.get(vert, None)

        # add new vertex, reuse index else
        if vert_index is None:
            vert_index = len(g3mesh.vertices)
            g3mesh.vertex_index[vert] = vert_index
            g3mesh.vertices.append(vert)

            if g3mesh.shape is not None:
                self._add_shapekeys(vert.original, g3mesh.shape)

        vert_index = vert_index % self.opt.max_vertices_per_mesh
        meshpart.indices.append(vert_index)

    def _add_shapekeys(self, vert: bpy.types.MeshVertex, shape: model.GShape):
        for key in shape.keys:
            key_vert = key.block.data[vert.index]
            key.positions.extend(key_vert.co)

    def _check_mesh_limits(self, g3mesh: G3MeshData):
        max = self.opt.max_vertices_per_mesh

        if len(g3mesh.vertices) > max:
            raise G3dError(f"The result mesh is too big {len(g3mesh.vertices)} > {max}")

        for meshpart in g3mesh.parts.values():
            if len(meshpart.indices) > max:
                log.warning("the result indices is too big %d > %d: %d", len(meshpart.indices), max, meshpart.id)
                break

    def _analyze_mesh(self, obj: bpy.types.Object,
                      mesh: bpy.types.Mesh,
                      armature: bpy.types.Object) -> MeshMetaInfo:
        """analyzes specified object to create optimal attribute flags"""
        meta = MeshMetaInfo(obj, mesh, armature)

        meta.attributes.append(PositionAttributeBuilder())

        if self.opt.use_shapekeys and mesh.shape_keys:
            meta.shape = model.GShape(mesh.name, mesh.shape_keys)

        if self.opt.use_normal:
            meta.attributes.append(NormalAttributeBuilder())

        if self.opt.use_tangent:
            meta.attributes.append(TangentAttributeBuilder())

        if self.opt.use_binormal:
            meta.attributes.append(BiTangentAttributeBuilder())

        color_layers = mesh.vertex_colors
        if self.opt.use_color and len(color_layers) > 0:
            if self.opt.packed_color:
                meta.attributes.append(PackedColorAttributeBuilder(color_layers))
            else:
                meta.attributes.append(ColorAttributeBuilder(color_layers))

        uv_layers = mesh.uv_layers
        if self.opt.use_uv and len(uv_layers) > 0:
            meta.attributes.append(UvAttributeBuilder(uv_layers, self.opt.flip_uv))

        if armature is not None:
            slots = obj.vertex_groups
            bones = armature.data.bones
            builder = BlendweightAttributeBuilder(slots, bones, 0, self.opt.max_bones_per_nodepart)
            builder.set_optimal_length(mesh, self.opt.bones_per_vertex)
            log.debug("set blendweights length %s: %d", mesh.name, builder.length)
            log.debug("set bones per nodepart %s: %d", mesh.name, builder.max_bones_per_nodepart)
            meta.attributes.append(builder)
        return meta

    def _get_material(self, mat: bpy.types.Material) -> model.GMaterial:
        """get or create material"""
        material = self.g3data.materials.get(mat.name, None)

        if material is None:
            material = self.material_builder.build(mat)
            self.g3data.materials[mat.name] = material
        return material

    def _get_g3mesh(self, attrs: MeshMetaInfo) -> G3MeshData:
        """get or create g3mesh data"""
        shape_id = attrs.shape.id if attrs.shape else None

        flags = attrs.flags()
        key = self._compute_gmesh_key(flags, shape_id)
        g3mesh = self.g3data.meshes.get(key, None)

        if not g3mesh:
            g3mesh = G3MeshData(flags)
            g3mesh.shape = attrs.shape
            self.g3data.meshes[key] = g3mesh
            log.debug("add g3mesh: %d = %s; shape: %s", key, g3mesh, g3mesh.shape is not None)

        return g3mesh

    @staticmethod
    def _compute_gmesh_key(flags: Tuple[model.VertexFlag], shape_id) -> int:
        return hash((flags, shape_id))

    def _get_nodepart(self, meta: MeshMetaInfo, mat: model.GMaterial,
                      g3mesh: G3MeshData, nodeparts: List[NodePartBuilder]) -> NodePartBuilder:
        """get or create nodepart"""
        nodepart = self._find_nodepart(meta.attributes, mat, nodeparts)

        if not nodepart:
            meshpartid = f"{meta.mesh.name}_part{len(g3mesh.parts)}"

            meshpart = MeshpartData(meshpartid, self.opt.primitive_type, g3mesh)
            g3mesh.parts[meshpartid] = meshpart

            nodepart = NodePartBuilder(mat, meshpart)
            nodeparts.append(nodepart)
            log.debug("%s add nodepart: %d", meta.obj.name, len(nodeparts))

        return nodepart

    def _find_nodepart(self, attrs: List[AttributeBuilder], mat: model.GMaterial,
                       parts: List[NodePartBuilder]) -> Union[NodePartBuilder, None]:
        """find part by material and bones included to it"""
        for part in parts:
            if part.material != mat:
                continue
            if self._filter_nodeparts(attrs, part):
                return part
        return None

    def _filter_nodeparts(self, attrs: List[AttributeBuilder], part: NodePartBuilder) -> bool:
        for attr in attrs:
            if not attr.filter_nodepart(part):
                return False
        return True


class NodeBuilder(object):
    """Creates spatial node"""
    def __init__(self, obj: bpy.types.Object):
        self.obj = obj

    def build(self) -> model.GNode:
        node = model.GNode(self.obj.name)

        mx: Matrix = self.obj.matrix_world
        if self.obj.parent:
            mx = self.obj.parent.matrix_world.inverted() @ mx

        (node.translation, node.rotation, node.scale) = mx.decompose()

        return node


class MeshNodeBuilder(NodeBuilder):
    """Creates node and parts by meshdata"""
    def __init__(self, obj: bpy.types.Object, meshdata: MeshNodeData):
        super().__init__(obj)
        self.meshdata = meshdata

    def build(self) -> model.GNode:
        node = super().build()
        if not self.meshdata:
            log.warning("meshnode has no meshdata: %s", node.id)
        else:
            for builder in self.meshdata.parts:
                node.parts.append(builder.build())
        return node


class ArmatureNodeBuilder(NodeBuilder):
    """Creates armature bones tree and bake animation"""
    def __init__(self, obj: bpy.types.Object, g3data: G3Data, opt: ModelOptions):
        super().__init__(obj)
        self.g3data = g3data
        self.opt = opt

    def build(self) -> model.GNode:
        node = super().build()

        self._add_armature_tree(node)

        if self.opt.use_actions:
            self._create_armature_animations(node)

        return node

    def _add_armature_tree(self, node: model.GNode):
        """build tree from root bones"""
        log.debug("build bones tree of %s", node.id)

        # data.bones are flatten from the roots
        for b_bone in self.obj.data.bones:
            if b_bone.parent is None:
                child = self._create_armature_bones_recursively(b_bone)
                node.children.append(child)

    def _create_armature_bones_recursively(self, bone: bpy.types.Bone) -> model.GNode:
        node = model.GNode(bone.name)
        rest: Matrix = bone.matrix_local

        if bone.parent:
            # relative to parent
            rest = bone.parent.matrix_local.inverted() @ bone.matrix_local

        (node.translation, node.rotation, node.scale) = rest.decompose()

        for child in bone.children:
            node.children.append(self._create_armature_bones_recursively(child))

        if self.opt.add_bone_tip and len(bone.children) == 0:
            tip = model.GNode(bone.name + '_end')
            tip.translation = Vector([0.0, bone.length, 0.0])
            tip.scale = Vector([1.0, 1.0, 1.0])
            tip.rotation = Quaternion([1.0, 0.0, 0.0, 0.0])
            node.children.append(tip)

        return node

    def _create_armature_animations(self, armature: model.GNode):
        for action in bpy.data.actions:
            if action.users == 0:
                continue

            anim = model.GAnimation(f'{armature.id}|{action.name}')

            if anim.id in self.g3data.animations:
                log.debug("skip handled animation: %s", anim.id)
                return

            for bone in self.obj.pose.bones:
                bone_anim = self._new_bone_animation(action, bone)

                if len(bone_anim.keyframes) > 0:
                    anim.bones.append(bone_anim)

            if len(anim.bones) > 0:
                log.debug("add animation: %s", anim.id)
                self.g3data.animations[anim.id] = anim

    def _new_bone_animation(self, action: bpy.types.Action, b_bone: bpy.types.PoseBone) -> model.GBoneAnimation:
        """
        Creates bone keyframes. Bakes for non-linear.
        The first keyframe will have 0 millis.
        Populates missing curves (location, rotation, scale) with the rest pose.

        Note that keyframe time from Graph Editor will be rounded to int.
        """

        anim_bone = model.GBoneAnimation(b_bone.name)

        if b_bone.name not in action.groups:
            return anim_bone

        bone_action = BoneAction(b_bone, action)

        keyframes: Dict[int, bool] = dict()

        # collect the time of all keyframes and decide which should be baked
        for curve in bone_action.curves():
            for keyframe in curve.keyframe_points:
                frame = int(keyframe.co[0])
                must_bake = keyframe.interpolation != 'LINEAR'
                # must_bake is always primary
                keyframes[frame] = must_bake or keyframes.get(frame, must_bake)

        timeline: List[int] = sorted(keyframes)

        for idx, frame in enumerate(timeline):
            eval_count = 1

            # check if we should bake to the next keyframe
            if keyframes[frame] and idx + 1 < len(timeline):
                eval_count = timeline[idx + 1] - frame

            for eval_idx in range(eval_count):
                cur_frame = frame + eval_idx
                # first keyframe is the start of animation so it's millis is 0
                millis = (1.0 / self.opt.fps) * 1000 * (cur_frame - timeline[0])

                pose = bone_action.eval_pose(cur_frame)
                key = model.GBoneKeyframe(millis, pose)
                anim_bone.keyframes.append(key)

        return anim_bone


class G3Builder(object):
    def __init__(self, opt: ModelOptions):
        self.opt = opt
        self.data = G3Data()
        self.meshdata_builder = MeshNodeDataBuilder(self.data, self.opt)

    def build(self) -> model.G3dModel:
        log.debug('start building...')
        root = bpy.context.view_layer.layer_collection

        for node in self._process_layer_collection(root):
            self.data.nodes.append(node)
            log.debug("add root node %s", node.id)

        return self._make()

    def _process_layer_collection(self,
                                  layer_col: bpy.types.LayerCollection) -> typing.Generator[model.GNode, None, None]:
        if layer_col.exclude:
            log.debug("skip hidden collection: %s", layer_col.name)
            return

        for node in self._process_collection(layer_col.collection, False, self.opt.selected_only):
            yield node

        for lc in layer_col.children:
            for node in self._process_layer_collection(lc):
                yield node

    def _process_collection(self, collection: bpy.types.Collection,
                            with_children: bool,
                            selected_only: bool) -> typing.Generator[model.GNode, None, None]:
        if collection.hide_viewport:
            log.debug("skip hidden collection: %s", collection.name)
            return

        log.debug('processing collection %s for %d objects...', collection.name, len(collection.objects))

        for obj in collection.objects:
            if not obj.parent or collection not in obj.parent.users_collection:
                for node in self._process_object(obj, selected_only):
                    yield node

        if with_children:
            for child in collection.children:
                for node in self._process_collection(child, with_children, selected_only):
                    yield node

    def _process_object(self, obj: bpy.types.Object,
                        selected_only: bool) -> typing.Generator[model.GNode, None, None]:

        if obj.hide_viewport:
            log.debug("skip hidden object: %s", obj.name)
            return

        if selected_only and not obj.select_get():
            log.debug("skip not selected object: %s", obj.name)
            return

        log.debug("process object %s/%d", obj.name, hash(obj))

        if obj.type == 'MESH':

            (eval_obj, eval_mesh) = evaluate(obj, self.opt.apply_modifiers)

            meshdata_key = hash(eval_mesh)
            meshdata = self.data.mesh_node_data.get(meshdata_key, None)

            if meshdata is None:
                armature = self._get_attached_armature(obj, selected_only)
                meshdata = self.meshdata_builder.build(eval_obj, eval_mesh, armature)
                self.data.mesh_node_data[meshdata_key] = meshdata

            node = MeshNodeBuilder(obj, meshdata).build()
            log.debug("new node %s", node.id)

            for child_obj in obj.children:
                for child_node in self._process_object(child_obj, selected_only):
                    node.children.append(child_node)
                    log.debug("add child node to %s: %s", node.id, child_node.id)

            yield node

        elif obj.type == 'ARMATURE':
            node = ArmatureNodeBuilder(obj, self.data, self.opt).build()
            log.debug("new node %s", node.id)

            for child_obj in obj.children:
                for child_node in self._process_object(child_obj, selected_only):
                    log.debug("handle armature child %s: %s", node.id, child_node.id)
                    # armature child should stay at the same level as armature
                    yield child_node

            yield node

        elif obj.type == 'EMPTY':
            node = NodeBuilder(obj).build()
            log.debug("new node %s", node.id)

            if obj.instance_collection is not None:
                for child_node in self._process_collection(obj.instance_collection, True, False):
                    node.children.append(child_node)
                    log.debug("add child node to %s: %s", node.id, child_node.id)
            else:
                for child_obj in obj.children:
                    for child_node in self._process_object(child_obj, False):
                        node.children.append(child_node)
                        log.debug("add child node to %s: %s", node.id, child_node.id)
            yield node
        else:
            log.debug("skip export for %s due type: %s", obj.name, obj.type)

    def _get_attached_armature(self, obj: bpy.types.Object, selected_only: bool) -> bpy.types.Object:
        """
        Ensures that the armature attached to the mesh object is also in the export list
        to be able to find optimal blendweight attributes count
        """
        if self.opt.use_armature:
            exist = obj.find_armature()
            if exist and not exist.hide_viewport and (not selected_only or obj.select_get()):
                return exist
        return None

    def _make(self) -> model.G3dModel:
        mod = model.G3dModel()

        self._make_meshes(mod)
        self._make_materials(mod)
        self._make_nodes(mod)
        self._make_animations(mod)
        self._make_shapekeys(mod)

        return mod

    def _make_meshes(self, mod: model.G3dModel):
        for g3mesh in self.data.meshes.values():
            mesh = model.GMesh(g3mesh.attributes)

            for v in g3mesh.vertices:
                mesh.vertices.extend(v.data)

            for part_builder in g3mesh.parts.values():
                part = model.GMeshPart(part_builder.id, part_builder.primitive_type)
                part.indices = part_builder.indices
                mesh.parts.append(part)

            mod.meshes.append(mesh)

    def _make_materials(self, mod: model.G3dModel):
        for mat in self.data.materials.values():
            mod.materials.append(mat)

    def _make_nodes(self, mod: model.G3dModel):
        if self.opt.y_up:
            rot = Quaternion((-0.707, 0.707, 0, 0))
            for node in self.data.nodes:
                node.rotation = rot @ node.rotation
                node.translation = rot @ node.translation

        mod.nodes = self.data.nodes

    def _make_animations(self, model: model.G3dModel):
        model.animations = list(self.data.animations.values())

    def _make_shapekeys(self, model: model.G3dModel):
        for mesh in self.data.meshes.values():
            if mesh.shape:
                model.shapes.append(mesh.shape)


class BoneAction(object):
    """Encapsulates valid curves"""

    def __init__(self, b_bone: bpy.types.PoseBone, action: bpy.types.Action) -> None:
        self.b_bone = b_bone
        self.loc_curves: List[bpy.types.FCurve] = []
        self.scale_curves: List[bpy.types.FCurve] = []
        self.quat_curves: List[bpy.types.FCurve] = []
        self.euler_curves: List[bpy.types.FCurve] = []

        for curve in action.groups[b_bone.name].channels:
            # TODO respect existing but disabled curves?
            if curve.data_path.endswith('location'):
                self.loc_curves.append(curve)
            elif curve.data_path.endswith('scale'):
                self.scale_curves.append(curve)
            elif curve.data_path.endswith('rotation_quaternion'):
                self.quat_curves.append(curve)
            elif curve.data_path.endswith('rotation_euler'):
                self.euler_curves.append(curve)

    def curves(self) -> List[bpy.types.FCurve]:
        return flatten([self.loc_curves, self.scale_curves, self.quat_curves, self.euler_curves])

    def eval_pose(self, frame: int) -> Matrix:
        loc = self._eval_curves(frame, self.loc_curves, Vector())
        scale = self._eval_curves(frame, self.scale_curves, Vector((1, 1, 1)))
        quat = self._eval_curves(frame, self.quat_curves, Quaternion())
        euler = self._eval_curves(frame, self.euler_curves, Euler())

        if self.b_bone.rotation_mode != 'QUATERNION':
            quat = euler.to_quaternion()

        trans = new_transorm_matrix(loc, quat, scale)
        rest = self.b_bone.bone.matrix_local

        if self.b_bone.parent:
            # relative to parent
            rest = self.b_bone.parent.bone.matrix_local.inverted() @ rest

        return rest @ trans

    def _eval_curves(self, frame: int,
                     curves: List[bpy.types.FCurve],
                     into: Union[Vector, Quaternion, Euler]) -> Union[Vector, Quaternion, Euler]:
        for curve in curves:
            into[curve.array_index] = curve.evaluate(frame)
        return into


def triangulate(mesh: bpy.types.Mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    del bm


def evaluate(obj: bpy.types.Object, apply_modifiers: bool) -> Tuple[bpy.types.Object, bpy.types.Mesh]:
    """Returns final triangulated mesh with applied object modifiers if it has no any shape keys"""
    apply_modifiers = apply_modifiers and obj.data.shape_keys is None
    log.debug("evaluate %s, apply modifiers %s", obj.name, apply_modifiers)

    if apply_modifiers:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        triangulate(obj_eval.data)
        return obj_eval, obj_eval.data

    mesh = obj.to_mesh()
    triangulate(mesh)
    return obj, mesh