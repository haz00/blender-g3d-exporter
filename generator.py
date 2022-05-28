# <pep8 compliant>

import bmesh
import bpy
from typing import Any, Dict, Tuple, Union, List
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from mathutils import Euler, Matrix, Quaternion, Vector

from domain import G3D, GAnimation, GBoneAnimation, GBoneKeyframe, GBoneMatrix, GMaterial, GMesh, GMeshPart, GNode, GNodePart, GShape, GShapeKey, GVertexAttribute

from utils import conv_uv, flatten, hash_vert, pack_color


class GMeshGeneratorOptions(object):
    """data used for cascade generation within single scene object"""

    def __init__(self, original: bpy.types.Object):
        self.original: bpy.types.Object = original
        # final triangulated mesh with applied object modifers if possible
        self.final_mesh: bpy.types.Mesh = None
        self.final_obj: bpy.types.Object = None
        self.color_layer: bpy.types.MeshLoopColorLayer = None
        self.uv_layer: bpy.types.MeshUVLoopLayer = None
        self.armature: bpy.types.Object = None
        self.max_blendweights: int = 0
        self.shape: GShape = None
        self.attributes: List[GVertexAttribute] = []


class GVertexBlendweightData(object):
    def __init__(self, part_bone_index: int, weight: float):
        self.part_bone_index = part_bone_index
        self.weight = weight


class G3dGenerator(object):

    def __init__(self) -> None:
        self.y_up = True
        self.use_normal = True
        self.use_color = True
        self.use_color_type = 'COLOR'
        self.use_uv = True
        self.use_tangent = True
        self.use_binormal = True
        self.flip_uv = True
        self.use_armature = True
        self.max_bones_per_vertex = 4
        self.use_shapekeys = True
        self.use_actions = True
        self.add_bone_tip = True
        self.apply_modifiers = True
        self.fps = bpy.context.scene.render.fps
        self.primitive_type = 'TRIANGLES'
        self.flat_nodes: Dict[str, GNode] = dict()

    def gen_node_part(self, node: GNode, mesh: GMesh, opt: GMeshGeneratorOptions, mat: GMaterial):
        mesh_part_id = f'{opt.original.data.name}_part{mat.index}'

        node_part = GNodePart(mat.id, mesh_part_id)
        node.parts.append(node_part)
        print(f'add materialid for {node.id}: {node_part.materialid}')
        
        if (mesh.get_mesh_part(mesh_part_id) == None):
            mesh_part = GMeshPart(mesh_part_id, self.primitive_type)
            mesh.parts.append(mesh_part)
            print(f'add meshpartid for {node.id}: {mesh_part.id}')

            self.gen_vertices(mesh, opt, mesh_part, node_part, mat.index)


    def normalize_blendweights(self, blendweights: List[GVertexBlendweightData]):
        total = sum(b.weight for b in blendweights)
        
        if (total > 0):
            for b in blendweights:
                b.weight /= total

    def gen_blendweights(self, node_part: GNodePart, vert: bpy.types.MeshVertex, opt: GMeshGeneratorOptions) -> List[float]:

        blendweights: List[GVertexBlendweightData] = []

        # search bone weight by each group assigned to vertex
        for vgroup in vert.groups:
            
            if (len(blendweights) == opt.max_blendweights):
                break

            group_index = vgroup.group
            group_name = opt.original.vertex_groups[group_index].name

            gbone = node_part.get_bone(group_name)

            if (gbone == None):
                # find bone by group name, register it if found 
                for bone in opt.armature.data.bones:
                    if (bone.name == group_name):
                        # TODO must be relative to armature or parent node?
                        gbone = GBoneMatrix(group_name, len(node_part.bones), bone.matrix_local)
                        node_part.bones.append(gbone)

            if (gbone != None):
                blendweights.append(GVertexBlendweightData(gbone.index, vgroup.weight))
        
        # necessary to add empty blendweights if array is not full yet
        for i in range(opt.max_blendweights - len(blendweights)):
            blendweights.append(GVertexBlendweightData(0, 0))

        self.normalize_blendweights(blendweights)

        # unwrap values to linear structure
        return flatten([[b.part_bone_index, b.weight] for b in blendweights])

    def gen_vertices(self, mesh: GMesh, opt: GMeshGeneratorOptions, mesh_part: GMeshPart, node_part: GMeshPart, mat_index: int):
        for polygon in opt.final_mesh.polygons:

            if (polygon.material_index != mat_index):
                continue

            for iv in range(len(polygon.vertices)):

                vert_index = polygon.vertices[iv]
                loop_index = polygon.loop_start + iv

                vert: bpy.types.MeshVertex = opt.final_mesh.vertices[vert_index]
                loop: bpy.types.MeshLoop = opt.final_mesh.loops[loop_index]

                vert_data: List[float] = []

                vert_data.extend(vert.co)

                if (self.use_normal):
                    vert_data.extend(vert.normal)

                if (self.use_tangent):
                    vert_data.extend(loop.tangent)

                if (self.use_binormal):
                    vert_data.extend(loop.bitangent)

                if (opt.color_layer != None):
                    col = opt.color_layer.data[loop_index].color # rgba
                    if (self.use_color_type == 'COLORPACKED'):
                        vert_data.append(pack_color(col))
                    else:
                        vert_data.extend(col)

                if (opt.uv_layer != None):
                    uv = opt.uv_layer.data[loop_index].uv
                    vert_data.extend(conv_uv(uv, self.flip_uv))

                if (opt.armature != None):
                    vert_data.extend(self.gen_blendweights(node_part, vert, opt))

                vhash = hash_vert(vert_data)

                # reuse index of similar vertex
                if (vhash not in mesh.vertex_index):
                    mesh.vertex_index[vhash] = len(mesh.vertices)
                    mesh.vertices.append(vert_data)

                    if (opt.shape != None):
                        for shape_key in opt.shape.keys:
                            key_vert = shape_key.source.data[vert_index]
                            shape_key.positions.append(key_vert.co)

                index = mesh.vertex_index[vhash]
                mesh_part.indices.append(index)

    def prepare_mesh(self, opt: GMeshGeneratorOptions):
        """Creates final triangulated mesh with applied object modifiers if possible"""
        if (self.use_shapekeys and opt.original.data.shape_keys):
            # mesh generated by modifiers cannot have shapekeys
            (opt.final_obj, opt.final_mesh) = self.evaluate(opt.original, False)
        else:
            (opt.final_obj, opt.final_mesh) = self.evaluate(opt.original, self.apply_modifiers)


    def analyze_mesh(self, opt: GMeshGeneratorOptions, use_armature: bool):
        """Populates vertex attributes flags and setup vertex generation settings"""
        
        opt.attributes = [GVertexAttribute('POSITION', 3)]

        if (self.use_shapekeys and opt.final_obj.data.shape_keys):
            # initialize shapekey slots
            opt.shape = GShape(opt.final_obj.data.name, opt.final_obj.data.shape_keys)

            print(f'{opt.final_obj.name} has shapekeys: {opt.shape.id}')

            for block in opt.final_obj.data.shape_keys.key_blocks:
                opt.shape.keys.append(GShapeKey(block.name, block))

        if (self.use_normal):
            opt.attributes.append(GVertexAttribute('NORMAL', 3))

        if (self.use_tangent):
            opt.attributes.append(GVertexAttribute('TANGENT', 3))

        if (self.use_binormal):
            opt.attributes.append(GVertexAttribute('BINORMAL', 3))

        color_layers = opt.final_mesh.vertex_colors
        if (self.use_color and len(color_layers) > 0):
            opt.color_layer = next(filter(lambda layer: layer.active_render, color_layers))

            if (self.use_color_type == 'COLORPACKED'):
                opt.attributes.append(GVertexAttribute('COLORPACKED', 1))
            else:
                opt.attributes.append(GVertexAttribute('COLOR', 4))

        uv_layers = opt.final_mesh.uv_layers
        if (self.use_uv and len(uv_layers) > 0):
            opt.uv_layer = next(filter(lambda layer: layer.active_render, uv_layers))
            opt.attributes.append(GVertexAttribute('TEXCOORD0', 2))

        # last armature modifier
        opt.armature = opt.final_obj.find_armature() if use_armature else None

        if (opt.armature != None):
            print(f'has armature: {opt.armature.name}')

            # find max groups assigned to any vertex
            for v in opt.final_mesh.vertices:
                opt.max_blendweights = max(opt.max_blendweights, len(v.groups))
                opt.max_blendweights = min(opt.max_blendweights, self.max_bones_per_vertex)

                if (opt.max_blendweights == self.max_bones_per_vertex):
                    break

            for i in range(opt.max_blendweights):
                opt.attributes.append(GVertexAttribute('BLENDWEIGHT' + str(i), 2))

    def gen_material(self, g3d: G3D, index: int, mat: bpy.types.Material) -> GMaterial:
        gmat = g3d.get_material(mat.name)

        if gmat == None:
            gmat = GMaterial(mat.name, index)
            gmat.setup_principled(PrincipledBSDFWrapper(mat.material, is_readonly=True))
            g3d.materials.append(gmat)
            print(f'add material: {gmat.id}')

        return gmat

    def gen_mesh_node(self, obj: bpy.types.Object, g3d: G3D, use_armature: bool):
        print(f'generate mesh node: {obj.name}')
        
        if (len(obj.material_slots) == 0):
            raise ValueError(f'{obj.name} has no materials')

        opt = GMeshGeneratorOptions(obj)
        self.prepare_mesh(opt)
        self.analyze_mesh(opt, use_armature)
        
        gmesh = g3d.get_mesh(opt.attributes, obj.data.name)

        # create gmesh if not exists
        if (gmesh == None):
            if (opt.shape != None):
                print(f"add shapekeys: {opt.shape.id}")
                g3d.shapes.append(opt.shape)

                gmesh = GMesh(opt.attributes, obj.data.name)
            else:
                gmesh = GMesh(opt.attributes, None)

            g3d.add_mesh(gmesh)

        node = self.gen_node(obj)

        # node part per material
        for i, mat in enumerate(obj.material_slots):
            gmat = self.gen_material(g3d, i, mat)
            self.gen_node_part(node, gmesh, opt, gmat)

    def gen_node(self, obj: bpy.types.Object) -> GNode:
        node = GNode(obj.name, obj)
        self.flat_nodes[node.id] = node
        print(f"add node: {node.id}")
        return node

    def gen_armature_node(self, obj: bpy.types.Object, g3d: G3D):
        print(f'generate armature node: {obj.name}')

        node = self.gen_node(obj)
        self.gen_armature_tree(node)

        if (self.use_actions):
            self.gen_armature_animations(node, g3d)

    def gen_armature_tree(self, node: GNode):
        """build tree from root bones"""
        print(f"generate bones for {node.id}: {len(node.source.data.bones)}")
        # data.bones are flatten
        for b_bone in node.source.data.bones:
            if (b_bone.parent == None):
                child = self.gen_armature_bones_recusvively(b_bone, self.add_bone_tip)
                node.children.append(child)

    def gen_armature_animations(self, node: GNode, g3d: G3D):
        for action in bpy.data.actions:
            if action.users == 0:
                continue

            anim = GAnimation(f'{node.id}|{action.name}')

            for bone in node.source.pose.bones:
                bone_anim = self.gen_bone_animation(action, bone)

                if (len(bone_anim.keyframes) > 0):
                    anim.bones.append(bone_anim)

            if (len(anim.bones) > 0):
                print(f"add animation: {anim.id}")
                g3d.animations.append(anim)

    def gen_armature_bones_recusvively(self, bone: bpy.types.Bone, add_tip: bool):
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
            node.children.append(self.gen_armature_bones_recusvively(child, add_tip))

        if (add_tip and len(bone.children) == 0):
            tip = GNode(bone.name + '_end', None)
            tip.translation = Vector([0.0, bone.length, 0.0])
            tip.scale = Vector([1.0, 1.0, 1.0])
            tip.rotation = Quaternion([1.0, 0.0, 0.0, 0.0])
            node.children.append(tip)

        return node

    def gen_bone_animation(self, action: bpy.types.Action, b_bone: bpy.types.PoseBone) -> GBoneAnimation:
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
                # first keyframe is start of animation so it millis is 0
                millis = (1.0 / self.fps) * 1000 * (cur_frame - timeline[0])

                pose = bone_action.eval_pose(cur_frame)
                key = GBoneKeyframe(millis, pose)
                anim_bone.keyframes.append(key)

        return anim_bone

    def tringalute(self, mesh: bpy.types.Mesh):
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        del bm


    def evaluate(self, obj: bpy.types.Object, apply_modifiers: bool) -> Tuple[bpy.types.Object, bpy.types.Mesh]:
        """returns temporal trinaluated mesh with applied modifiers"""
        print(f"evaluate {obj.name}, apply modifiers {apply_modifiers}")

        if (apply_modifiers):
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            self.tringalute(obj_eval.data)
            return (obj_eval, obj_eval.data)

        mesh = obj.to_mesh()
        self.tringalute(mesh)
        return (obj, mesh)

    def generate(self, objects: List[bpy.types.Object]) -> G3D:
        print(f'generate: objects count: {len(objects)}')
        
        g3d = G3D()

        for obj in objects:

            if (not obj.visible_get()):
                print(f"skip not visible: {obj.name}")
                continue

            obj.update_from_editmode()

            if (obj.type == 'ARMATURE'):
                if (self.use_armature):
                    self.gen_armature_node(obj, g3d)

            elif (obj.type == 'MESH'):
                # ensure the attached armature is also in export list - requires to blendweights
                armature_selected = obj.find_armature() in objects if (self.use_armature) else False

                self.gen_mesh_node(obj, g3d, armature_selected)

            else:
                print(f'not supported export type for {obj.name}: {obj.type}')

        self.resolve_nodes_tree(g3d)

        # rotate root nodes
        if (self.y_up):
            y_up = Quaternion([-0.707107, 0.707107, 0.000000,  0.000000])
            for root in g3d.nodes:
                root.rotation = y_up @ root.rotation 
                root.translation = y_up @ root.translation 

        print('generated')
        return g3d
    
    def resolve_nodes_tree(self, g3d: G3D):
        """assotiate parent-child node relations"""

        for k in self.flat_nodes:
            node = self.flat_nodes[k]

            for b_child in node.source.children:
                if (b_child.name in self.flat_nodes):

                    # but not for armature's children with armature modifier
                    # they should stay in root
                    if (node.source.type == 'ARMATURE' and b_child.find_armature() != None):
                        continue

                    child = self.flat_nodes[b_child.name]

                    node.children.append(child)
                    child.parent = node

        # nodes without parent going to root
        for k in self.flat_nodes:
            node = self.flat_nodes[k]
            if (node.parent == None):
                g3d.nodes.append(node)
        
        self.flat_nodes.clear()


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
        
        loc = self.eval_curves(frame, self.loc_curves, Vector())
        scale = self.eval_curves(frame, self.scale_curves, Vector((1, 1, 1)))
        quat = self.eval_curves(frame, self.quat_curves, Quaternion())
        euler = self.eval_curves(frame, self.euler_curves, Euler())
        
        if (self.b_bone.rotation_mode != 'QUATERNION'):
            quat = euler.to_quaternion()

        trans = Matrix.LocRotScale(loc, quat, scale)
        rest = self.b_bone.bone.matrix_local

        if (self.b_bone.parent):
            # relative to parent
            rest = self.b_bone.parent.bone.matrix_local.inverted() @ rest

        return rest @ trans

    def eval_curves(self, frame: int, curves: List[bpy.types.FCurve], into: Union[Vector, Quaternion, Euler]) -> Union[Vector, Quaternion, Euler]:
        for curve in curves: 
            into[curve.array_index] = curve.evaluate(frame)
        return into
