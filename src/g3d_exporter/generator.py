# <pep8 compliant>

import bpy
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.node_shader_utils import ShaderImageTextureWrapper

from typing import Any, Dict, Set, Tuple, Union, List, Iterable
import os

from .model import *
from .common import *

class G3dBuilder(object):

    def __init__(self, candidates: List[bpy.types.Object]) -> None:
        self.candidates = candidates
        self.model = G3dModel()
        self.y_up = True
        self.use_normal = True
        self.use_color = True
        self.packed_color = True
        self.use_uv = True
        self.use_tangent = True
        self.use_binormal = True
        self.flip_uv = True
        self.use_armature = True
        self.max_bones_per_vertex = 4
        self.max_bones_per_nodepart = 12
        self.max_vertices = 32000
        self.use_shapekeys = True
        self.use_actions = True
        self.add_bone_tip = True
        self.apply_modifiers = True
        self.fps = bpy.context.scene.render.fps
        self.primitive_type = 'TRIANGLES'
        self._flat_nodes: Dict[str, GNode] = dict()


    def add_material(self, mat: bpy.types.Material) -> GMaterial:
        gmat = self.model.get_material(mat.name)

        if gmat == None:
            gmat = GMaterial(mat.name)
            self.setup_principled(gmat, PrincipledBSDFWrapper(mat, is_readonly=True))
            self.model.materials[gmat.id] = gmat
            print(f'add material: {gmat.id}')

        return gmat


    def handle_mesh_node(self, obj: bpy.types.Object, armature: bpy.types.Object):
        print(f'generate mesh node: {obj.name}')
        
        if (len(obj.material_slots) == 0):
            raise G3dError(f'{obj.name} has no materials')

        (final_obj, final_mesh) = self.evaluate(obj, self.apply_modifiers)
        
        node = self.add_node(obj)

        builder = GMeshBuilder(self, node, armature, final_obj, final_mesh)

        mesh = self.model.get_mesh(builder.attributes, obj.data.name, builder.shape != None)

        if (mesh == None):
            mesh = GMesh(builder.attributes, obj.data.name)
            self.model.add_mesh(mesh)

            if (builder.shape != None):
                print(f"add shapekeys: {builder.shape.id}")
                self.model.shapes.append(builder.shape)

        builder.populate_mesh(mesh)


    def add_node(self, obj: bpy.types.Object) -> GNode:
        node = GNode(obj.name, obj)
        self._flat_nodes[node.id] = node
        print(f"add node: {node.id}")
        return node


    def handle_armature_node(self, obj: bpy.types.Object):
        print(f'generate armature node: {obj.name}')

        node = self.add_node(obj)
        self.create_armature_tree(node)

        if (self.use_actions):
            self.handle_armature_animations(node)


    def create_armature_tree(self, node: GNode):
        """build tree from root bones"""
        print(f"generate bones for {node.id}: {len(node.source.data.bones)}")
        # data.bones are flatten from the roots
        for b_bone in node.source.data.bones:
            if (b_bone.parent == None):
                child = self.create_armature_bones_recusvively(b_bone, self.add_bone_tip)
                node.children.append(child)


    def handle_armature_animations(self, node: GNode):
        for action in bpy.data.actions:
            if action.users == 0:
                continue

            anim = GAnimation(f'{node.id}|{action.name}')

            for bone in node.source.pose.bones:
                bone_anim = self.new_bone_animation(action, bone)

                if (len(bone_anim.keyframes) > 0):
                    anim.bones.append(bone_anim)

            if (len(anim.bones) > 0):
                print(f"add animation: {anim.id}")
                self.model.animations.append(anim)


    def create_armature_bones_recusvively(self, bone: bpy.types.Bone, add_tip: bool):
        node = GNode(bone.name, None)
        rest: Matrix = bone.matrix_local

        if (bone.parent):
            # relative to parent
            rest = bone.parent.matrix_local.inverted() @ bone.matrix_local

        (t, r, s) = rest.decompose()

        node.translation = t
        node.scale = s
        node.rotation = r

        for child in bone.children:
            node.children.append(self.create_armature_bones_recusvively(child, add_tip))

        if (add_tip and len(bone.children) == 0):
            tip = GNode(bone.name + '_end', None)
            tip.translation = Vector([0.0, bone.length, 0.0])
            tip.scale = Vector([1.0, 1.0, 1.0])
            tip.rotation = Quaternion([1.0, 0.0, 0.0, 0.0])
            node.children.append(tip)

        return node


    def new_bone_animation(self, action: bpy.types.Action, b_bone: bpy.types.PoseBone) -> GBoneAnimation:
        """
        Creates bone keyframes. Bakes for non-linear. 
        The first keyframe will have 0 millis. 
        Populates missing curves (location, rotation, scale) with the rest pose.

        Note that keyframe time from Graph Editor will be rounded to int.
        """

        anim_bone = GBoneAnimation(b_bone.name)

        if (b_bone.name not in action.groups):
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
            if (keyframes[frame] and idx + 1 < len(timeline)):
                eval_count = timeline[idx + 1] - frame
            
            for eval_idx in range(eval_count):
                cur_frame = frame + eval_idx
                # first keyframe is the start of animation so it's millis is 0
                millis = (1.0 / self.fps) * 1000 * (cur_frame - timeline[0])

                pose = bone_action.eval_pose(cur_frame)
                key = GBoneKeyframe(millis, pose)
                anim_bone.keyframes.append(key)

        return anim_bone


    def generate(self) -> G3dModel:
        print(f'generate: candidates count: {len(self.candidates)}')

        for obj in self.candidates:
            self._handle_candidate(obj)

        self.resolve_nodes_tree()

        if self.y_up:
            # rotate root nodes
            self.conv_rotation(Quaternion([-0.707107, 0.707107, 0.000000,  0.000000]))

        print('generated')
        return self.model
    

    def _handle_candidate(self, obj: bpy.types.Object):
        if not obj.visible_get():
            print(f"skip not visible: {obj.name}")
            return

        obj.update_from_editmode()

        if obj.type == 'ARMATURE':
            if (self.use_armature):
                self.handle_armature_node(obj)

        elif obj.type == 'MESH':
            armature = self.get_attached_armature(obj)

            self.handle_mesh_node(obj, armature)

        elif obj.instance_collection != None:
            # if collection instance
                # obj.instance_collection.all_objects
                # TODO collection instance
            pass

        else:
            print(f'not supported export type for {obj.name}: {obj.type}')


    def get_attached_armature(self, obj: bpy.types.Object) -> bpy.types.Object:
        """
        Ensures that the attached armature is also in export list to able find optimal blendweights count
        """
        if self.use_armature:
            exist = obj.find_armature()
            if exist and exist.visible_get() and exist in self.candidates:
                return exist
        return None



    def tringalute(self, mesh: bpy.types.Mesh):
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        del bm


    def evaluate(self, obj: bpy.types.Object, apply_modifiers: bool) -> Tuple[bpy.types.Object, bpy.types.Mesh]:
        """
        Returns final triangulated mesh with applied object modifiers if possible.
        Modifier cannot be applied to a mesh with shape keys.
        """
        apply_modifiers = apply_modifiers and obj.data.shape_keys == None

        print(f"evaluate {obj.name}, apply modifiers {apply_modifiers}")

        if (apply_modifiers):
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            self.tringalute(obj_eval.data)
            return (obj_eval, obj_eval.data)

        mesh = obj.to_mesh()
        self.tringalute(mesh)
        return (obj, mesh)


    def conv_rotation(self, rot: Quaternion):
        for root in self.model.nodes:
            root.rotation = rot @ root.rotation 
            root.translation = rot @ root.translation 


    def resolve_nodes_tree(self):
        """assotiate parent-child node relations"""
        for k in self._flat_nodes:
            node = self._flat_nodes[k]

            for b_child in node.source.children:
                if (b_child.name in self._flat_nodes):

                    # but not for armature's children with armature modifier
                    # they should stay in root
                    if (node.source.type == 'ARMATURE' and b_child.find_armature() != None):
                        continue

                    child = self._flat_nodes[b_child.name]

                    node.children.append(child)
                    child.parent = node

        # nodes without parent going to root
        for k in self._flat_nodes:
            node = self._flat_nodes[k]
            if (node.parent == None):
                self.model.nodes.append(node)
        
        self._flat_nodes.clear()


    def setup_principled(self, mat: GMaterial, bsdf: PrincipledBSDFWrapper):
        """uses active output and connected Principled BSDF node sockets to collect infomation"""
        if (not self.setup_texture(mat, 'TRANSPARENCY', bsdf.alpha_texture)):
            mat.opacity = bsdf.alpha

        if (not self.setup_texture(mat, 'DIFFUSE', bsdf.base_color_texture)):
            mat.diffuse = unwrapv(bsdf.base_color)

        if (not self.setup_texture(mat, 'EMISSIVE', bsdf.emission_color_texture)):
            mat.emissive = unwrapv(bsdf.emission_color)

        if (not self.setup_texture(mat, 'SHININESS', bsdf.roughness_texture)):
            mat.shininess = 1.0 - bsdf.roughness

        if (not self.setup_texture(mat, 'SPECULAR', bsdf.specular_texture)):
            mat.specular = [bsdf.specular, bsdf.specular, bsdf.specular]

        if (not self.setup_texture(mat, 'REFLECTION', bsdf.metallic_texture)):
            mat.reflection = [bsdf.metallic, bsdf.metallic, bsdf.metallic]

        self.setup_texture(mat, 'NORMAL', bsdf.normalmap_texture)

        # TODO also look for nodes
        if (not bpy.context.scene.world.use_nodes):
            mat.ambient = unwrapv(bpy.context.scene.world.color)


    def setup_texture(self, mat: GMaterial, type: str, wrapper: ShaderImageTextureWrapper) -> bool:
        if (wrapper and wrapper.image and wrapper.image.source == 'FILE'):
            filename = os.path.basename(wrapper.image.filepath_from_user())
            tex = GTexture(wrapper.image.name, type, filename, wrapper.image)
            mat.textures.append(tex)
            print(f"add texture {tex}")
            return True
        return False


class GVertexBlendweightBuilder(object):
    def __init__(self, group: str, weight: float):
        """If blendweught is stub the group may be None"""
        self.part_bone_index = 0
        self.weight = weight
        self.group = group


    def update_indices(self, bones: Dict[str, GBoneMatrix]):
        if self.group == None:
            self.weight = 0.0
            self.part_bone_index = 0
            return

        if self.group not in bones:
            raise ValueError(f"Group '{self.group}' not found in: {', '.join(bones)}")
            
        self.part_bone_index = bones[self.group].index


    def build(self) -> List[float]:
        return [float(self.part_bone_index), self.weight]


class GVertexBuilder(object):
    def __init__(self, source: bpy.types.MeshVertex) -> None:
        self.source = source
        self.position: List[float] = None
        self.normal: List[float] = None
        self.tangent: List[float] = None
        self.bitangent: List[float] = None
        self.color: List[float] = None
        self.color_packed: float = None
        self.texCoord0: List[float] = None
        self.blendweights: List[GVertexBlendweightBuilder] = None


    def update_blendweight_indices(self, bones: Dict[str, GBoneMatrix]):
        for w in self.blendweights:
            w.update_indices(bones)
                    

    def build(self) -> List[float]:
        data = list(self.position)
        if self.normal:
            data.extend(self.normal)
        if self.tangent:
            data.extend(self.tangent)
        if self.bitangent:
            data.extend(self.bitangent)
        if self.color:
            data.extend(self.color)
        if self.color_packed:
            data.extend(self.color_packed)
        if self.texCoord0:
            data.extend(self.texCoord0)
        if self.blendweights:
            for w in self.blendweights:
                data.extend(w.build())
        return data


class GMeshBuilder(object):
    """populates mesh by specified scene object"""
    def __init__(self, opt: G3dBuilder, node: GNode, armature: bpy.types.Object, final_object: bpy.types.Object, final_mesh: bpy.types.Mesh):
        self.opt = opt
        self.node = node
        self.final_object = final_object
        self.final_mesh = final_mesh
        self.color_layer: bpy.types.MeshLoopColorLayer = None
        self.uv_layer: bpy.types.MeshUVLoopLayer = None
        self.armature = armature
        self.max_blendweights: int = 0
        self.shape: GShape = None
        self.attributes: List[GVertexAttribute] = self._setup_attributes()
        self.meshparts_completed: Set[str] = set()


    def _setup_attributes(self) -> List[GVertexAttribute]:
        """analyzes specified object to create optimal attributes flags"""     
        attributes: List[GVertexAttribute] = list()
        attributes.append(GVertexAttribute('POSITION', 3))

        if (self.opt.use_shapekeys and self.final_object.data.shape_keys):
            # initialize shapekey slots
            self.shape = GShape(self.final_object.data.name, self.final_object.data.shape_keys)

            print(f'{self.final_object.name} has shapekeys: {self.shape.id}')

            for block in self.final_object.data.shape_keys.key_blocks:
                self.shape.keys.append(GShapeKey(block.name, block))

        if (self.opt.use_normal):
            attributes.append(GVertexAttribute('NORMAL', 3))

        if (self.opt.use_tangent):
            attributes.append(GVertexAttribute('TANGENT', 3))

        if (self.opt.use_binormal):
            attributes.append(GVertexAttribute('BINORMAL', 3))

        color_layers = self.final_mesh.vertex_colors
        if (self.opt.use_color and len(color_layers) > 0):
            self.color_layer = next(filter(lambda layer: layer.active_render, color_layers))

            if (self.packed_color):
                attributes.append(GVertexAttribute('COLORPACKED', 1))
            else:
                attributes.append(GVertexAttribute('COLOR', 4))

        uv_layers = self.final_mesh.uv_layers
        if (self.opt.use_uv and len(uv_layers) > 0):
            self.uv_layer = next(filter(lambda layer: layer.active_render, uv_layers))
            attributes.append(GVertexAttribute('TEXCOORD0', 2))

        if (self.armature != None):
            print(f'has armature: {self.armature.name}')

            # find max groups assigned to any vertex to make selfimal count of attributes
            for v in self.final_mesh.vertices:
                self.max_blendweights = max(self.max_blendweights, len(v.groups))
                self.max_blendweights = min(self.max_blendweights, self.opt.max_bones_per_vertex)

                if (self.max_blendweights == self.opt.max_bones_per_vertex):
                    break

            for i in range(self.max_blendweights):
                attributes.append(GVertexAttribute('BLENDWEIGHT' + str(i), 2))

        return attributes


    def _count_bone_matches(self, nodepart: GNodePart, bones: Set[str]) -> int:
        if not nodepart.bones or not bones:
            return 0

        matches = 0
        for name in bones:
            if nodepart.get_bone(name):
                matches += 1
        return matches


    def _populate_bones(self, nodepart: GNodePart, bones: Set[str]):
        if not bones:
            return

        for name in bones:
            if not nodepart.get_bone(name):
                bone = self.armature.data.bones[name]
                nodepart.add_bone(GBoneMatrix(name, bone.matrix_local))


    def _find_nodepart(self, mat: GMaterial, bones: Set[str] = None) -> GNodePart:
        # seach nodepart by material, create new if not found
        for nodepart in self.node.parts:
            
            if nodepart.material.id != mat.id:
                continue

            if not bones:
                return nodepart

            # make sure that all the bones from blendweights are present in nodepart's bones             
            matches_count = self._count_bone_matches(nodepart, bones)
            rest_count = len(bones) - matches_count

            # shortage - add if there is enough space, bust - create a new nodepart
            if len(nodepart.bones) + rest_count <= self.opt.max_bones_per_nodepart:
                self._populate_bones(nodepart, bones)
                return nodepart

        return None


    def _find_uniq_bones(self, face: List[GVertexBuilder]) -> Set[str]:
        bones: Set[str] = set()

        for vert in face:
            if vert.blendweights:
                for w in vert.blendweights:
                    if w.group:
                        bones.add(w.group)

        return bones


    def populate_mesh(self, mesh: GMesh):   
        new_meshparts = set()

        for polygon in self.final_mesh.polygons:
            
            bmat = self.node.source.material_slots[polygon.material_index].material
            gmat = self.opt.add_material(bmat)

            face = self._build_face(polygon)
            uniq_bones = self._find_uniq_bones(face) if (self.armature) else None

            nodepart = self._find_nodepart(gmat, uniq_bones)
            if not nodepart:
                # TODO what with linked mesh?
                meshpartid = f"{self.node.source.data.name}_part{len(self.node.parts)}"

                # create meshpart if needed
                meshpart = mesh.get_meshpart(meshpartid)
                if not meshpart:
                    meshpart = mesh.add_part(GMeshPart(meshpartid, self.opt.primitive_type))
                    new_meshparts.add(meshpartid)
                    
                nodepart = GNodePart(gmat, meshpart) 
                self._populate_bones(nodepart, uniq_bones)
                self.node.parts.append(nodepart)
            
            if nodepart.meshpart.id in self.meshparts_completed:
                continue

            # populate mesh and mesh part
            for vert in face:
                # update bone indexes in blendweights by group name
                if vert.blendweights:
                    vert.update_blendweight_indices(nodepart.bones)

                # cache vertex to reuse index
                vert_data = vert.build()
                vhash = hash_vert(vert_data)
                
                if (vhash not in mesh.vertex_index):
                    mesh.vertex_index[vhash] = len(mesh.vertices)
                    mesh.vertices.append(vert_data)

                    # add shapekeys for this vertex 
                    if (self.shape != None):
                        for shape_key in self.shape.keys:
                            key_vert = shape_key.source.data[vert.source.index]
                            shape_key.positions.append(key_vert.co)

                vert_index = mesh.vertex_index[vhash]
                nodepart.meshpart.indices.append(vert_index)

            self.validate_mesh_limits(len(mesh.vertices), len(meshpart.indices))

        self.meshparts_completed.update(new_meshparts)


    def validate_mesh_limits(self, verts, idx):
        if verts < self.opt.max_vertices and idx < self.opt.max_vertices:
            return

        msg = f"Mesh limits exceeded ({self.opt.max_vertices}): vertices: {verts}, indicies: {idx}"
        raise G3dError(msg)


    def _norm_blendweights(self, blendweights: List[GVertexBlendweightBuilder]):
        total = sum(b.weight for b in blendweights)
        
        if (total > 0):
            for b in blendweights:
                b.weight /= total


    def _gen_blendweights(self, vert: bpy.types.MeshVertex) -> List[GVertexBlendweightBuilder]:
        blendweights: List[GVertexBlendweightBuilder] = list()

        # search bone weight by each group assigned to vertex
        for vgroup in vert.groups:
            
            if len(blendweights) == self.max_blendweights:
                break

            group_index = vgroup.group
            group_name = self.node.source.vertex_groups[group_index].name

            # ensures that the group is real bone 
            if group_name in self.armature.data.bones:
                blendweights.append(GVertexBlendweightBuilder(group_name, vgroup.weight))
        
        # its necessary to add empty blendweights if the array is not full yet
        for _ in range(self.max_blendweights - len(blendweights)):
            blendweights.append(GVertexBlendweightBuilder(None, 0.0))

        self._norm_blendweights(blendweights)
        return blendweights


    def _build_face(self, polygon: bpy.types.MeshPolygon) -> List[GVertexBuilder]:
        face = list()

        for iv in range(len(polygon.vertices)):

            vert_index = polygon.vertices[iv]
            loop_index = polygon.loop_start + iv

            vert: bpy.types.MeshVertex = self.final_mesh.vertices[vert_index]
            loop: bpy.types.MeshLoop = self.final_mesh.loops[loop_index]

            builder = GVertexBuilder(vert)
            builder.position = vert.co

            if (self.opt.use_normal):
                builder.normal = vert.normal

            if (self.opt.use_tangent):
                builder.tangent = loop.tangent

            if (self.opt.use_binormal):
                builder.bitangent = loop.bitangent

            if (self.color_layer != None):
                col = self.color_layer.data[loop_index].color # rgba
                if (self.opt.packed_color):
                    builder.color_packed = pack_color(col)
                else:
                    builder.color = col

            if (self.uv_layer != None):
                uv = self.uv_layer.data[loop_index].uv
                builder.texCoord0 = conv_uv(uv, self.opt.flip_uv)

            if (self.armature != None):
                builder.blendweights = self._gen_blendweights(vert)

            face.append(builder)
            
        return face


class BoneAction(object):
    """Encapsulates valid action curves of bone"""
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
        
        if (self.b_bone.rotation_mode != 'QUATERNION'):
            quat = euler.to_quaternion()

        trans = new_transorm_matrix(loc, quat, scale)
        rest = self.b_bone.bone.matrix_local

        if (self.b_bone.parent):
            # relative to parent
            rest = self.b_bone.parent.bone.matrix_local.inverted() @ rest

        return rest @ trans


    def _eval_curves(self, frame: int, curves: List[bpy.types.FCurve], into: Union[Vector, Quaternion, Euler]) -> Union[Vector, Quaternion, Euler]:
        for curve in curves: 
            into[curve.array_index] = curve.evaluate(frame)
        return into

