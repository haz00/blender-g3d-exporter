# <pep8 compliant>

import bmesh
import bpy
import typing
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from mathutils import Euler, Matrix, Quaternion, Vector

from domain import G3D, GAnimation, GBoneAnimation, GBoneKeyframe, GBoneMatrix, GMaterial, GMesh, GMeshPart, GNode, GNodePart, GShape, GShapeKey, GVertexAttribute

from utils import conv_uv, flatten, hash_vert, pack_color


class GMeshGeneratorOptions(object):
    """data used for cascade generation within single scene object"""

    def __init__(self):
        self.original: bpy.types.Object = None
        # final triangulated object with applyed modifers if possible
        self.final_mesh: bpy.types.Mesh = None
        self.final_obj: bpy.types.Object = None
        self.color_layer: bpy.types.MeshLoopColorLayer = None
        self.uv_layer: bpy.types.MeshUVLoopLayer = None
        self.armature: bpy.types.Object = None
        self.max_blendweights: int = 0
        self.shape: GShape = None


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
        self.flat_nodes: dict[str, GNode] = dict()

    def new_material(self, mat: bpy.types.Material, index: int) -> GMaterial:
        gmat = GMaterial(mat.name, index)
        gmat.setup_principled(PrincipledBSDFWrapper(mat.material, is_readonly=True))
        return gmat

    def gen_node_part(self, node: GNode, mesh: GMesh, opt: GMeshGeneratorOptions, mat: GMaterial):
        # TODO reuse mesh part by using blender mesh 
        mesh_part = GMeshPart(f'{node.id}_part{mat.index}', self.primitive_type)
        mesh.parts.append(mesh_part)
        print(f'add mesh part: {mesh_part.id}')

        node_part = GNodePart(mat.id, mesh_part.id)
        node.parts.append(node_part)
        print(f'add node part: {node_part.materialid} {node_part.meshpartid}')

        self.gen_vertices(mesh, opt, mesh_part, node_part, mat.index)

    def normalize_blendweights(self, blendweights: list[GVertexBlendweightData]):
        total = sum(b.weight for b in blendweights)
        
        for b in blendweights:
            b.weight /= total

    def gen_blendweights(self, node_part: GNodePart, vert: bpy.types.MeshVertex, opt: GMeshGeneratorOptions) -> list[float]:

        blendweights: list[GVertexBlendweightData] = []

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

                vert_data: list[float] = []

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

    def prepare_gmesh(self, g3d: G3D, obj: bpy.types.Object, use_armature: bool) -> typing.Tuple[GMesh, GMeshGeneratorOptions]:
        """analyzes attributes, triangulates and creates mesh if needed"""

        if (len(obj.material_slots) == 0):
            raise ValueError(f'{obj.name} has no materials')

        mesh: GMesh = None
        opt = GMeshGeneratorOptions()
        attributes = [GVertexAttribute('POSITION', 3)]

        opt.original = obj

        # if there are shapekeys always add dedicated mesh to keep vertex ordering
        if (self.use_shapekeys and obj.data.shape_keys):
            print(f'{obj.name} has shapekes')

            # initialize shapekey slots
            opt.shape = GShape(obj.name, obj.data.shape_keys)

            for block in obj.data.shape_keys.key_blocks:
                opt.shape.keys.append(GShapeKey(block.name, block))

            g3d.shapes.append(opt.shape)

            mesh = GMesh(attributes, False)
            g3d.add_mesh(mesh)

            # mesh generated by modifiers cannot have shapekeys
            (opt.final_obj, opt.final_mesh) = self.evaluate(obj, False)

        else:
            (opt.final_obj, opt.final_mesh) = self.evaluate(obj, self.apply_modifiers)


        if (self.use_normal):
            attributes.append(GVertexAttribute('NORMAL', 3))

        if (self.use_tangent):
            attributes.append(GVertexAttribute('TANGENT', 3))

        if (self.use_binormal):
            attributes.append(GVertexAttribute('BINORMAL', 3))

        if (self.use_color and len(opt.final_mesh.vertex_colors) > 0):
            opt.color_layer = next(filter(lambda layer: layer.active_render, opt.final_mesh.vertex_colors))

            if (self.use_color_type == 'COLORPACKED'):
                attributes.append(GVertexAttribute('COLORPACKED', 1))
            else:
                attributes.append(GVertexAttribute('COLOR', 4))
                

        if (self.use_uv and len(opt.final_mesh.uv_layers) > 0):
            opt.uv_layer = next(
                filter(lambda layer: layer.active_render, opt.final_mesh.uv_layers))
            attributes.append(GVertexAttribute('TEXCOORD0', 2))

        # last armature modifier
        opt.armature = obj.find_armature() if use_armature else None

        if (opt.armature != None):
            print(f'has armature: {opt.armature.name}')

            for v in opt.final_mesh.vertices:
                opt.max_blendweights = max(opt.max_blendweights, len(v.groups))
                opt.max_blendweights = min(
                    opt.max_blendweights, self.max_bones_per_vertex)

                if (opt.max_blendweights == self.max_bones_per_vertex):
                    break

            for i in range(opt.max_blendweights):
                attributes.append(GVertexAttribute('BLENDWEIGHT' + str(i), 2))

        if (mesh != None):
            return mesh, opt

        for m in g3d.meshes:
            if (m.open and m.attributes == attributes):
                return m, opt

        mesh = GMesh(attributes, True)
        g3d.add_mesh(mesh)
        return mesh, opt


    def gen_mesh_node(self, obj: bpy.types.Object, g3d: G3D, use_armature: bool):
        print(f'generate mesh: {obj.name}')
        
        (gmesh, options) = self.prepare_gmesh(g3d, obj, use_armature)

        node = self.add_node(obj)

        # node part per material
        for i in range(len(obj.material_slots)):

            mat = obj.material_slots[i]

            gmat = g3d.get_material(mat.name)
            if gmat == None:
                gmat = self.new_material(mat, i)
                g3d.materials.append(gmat)
                print(f'add material: {gmat.id}')

            self.gen_node_part(node, gmesh, options, gmat)

    def add_node(self, obj: bpy.types.Object) -> GNode:
        node = GNode(obj.name, obj)
        self.flat_nodes[node.id] = node
        print(f"add node: {node.id}")
        return node

    def gen_armature_node(self, obj: bpy.types.Object, g3d: G3D):
        print(f'generate armature: {obj.name}')

        node = self.add_node(obj)
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

            for bone in node.source.data.bones:
                baked = self.bake_bone_animation(action, bone)

                if (len(baked.keyframes) > 0):
                    anim.bones.append(baked)

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

    def bake_bone_animation(self, action: bpy.types.Action, b_bone: bpy.types.Bone) -> GBoneAnimation:

        # blender stores curves in arrays as:
        #    x = ['Bone'].translation
        #    y = ['Bone'].translation
        #    z = ['Bone'].translation
        #    x = ['Bone'].scale
        #    ...

        pos_curves: list[bpy.types.FCurve] = []
        scale_curves: list[bpy.types.FCurve] = []
        quat_curves: list[bpy.types.FCurve] = []
        euler_curves: list[bpy.types.FCurve] = []

        # we need to bake curves with one length
        # if curve is not exists the default values will be used
        start_frame: int = 0
        end_frame: int = 0

        # find curves in this action
        for group in action.groups:
            if (group.name == b_bone.name):
                for curve in group.channels:
                    if (curve.data_path.endswith('location')):
                        pos_curves.append(curve)
                        start_frame = int(min(start_frame, curve.range()[0]))
                        end_frame = int(max(end_frame, curve.range()[1]))
                    elif (curve.data_path.endswith('scale')):
                        scale_curves.append(curve)
                        start_frame = int(min(start_frame, curve.range()[0]))
                        end_frame = int(max(end_frame, curve.range()[1]))
                    elif (curve.data_path.endswith('rotation_quaternion')):
                        quat_curves.append(curve)
                        start_frame = int(min(start_frame, curve.range()[0]))
                        end_frame = int(max(end_frame, curve.range()[1]))
                    elif (curve.data_path.endswith('rotation_euler')):
                        euler_curves.append(curve)
                        start_frame = int(min(start_frame, curve.range()[0]))
                        end_frame = int(max(end_frame, curve.range()[1]))
                break

        def bake(frame: int, curve_axis: list[bpy.types.FCurve], into_axis: typing.Union[Vector, Euler, Quaternion]):
            for i in range(len(curve_axis)):
                into_axis[i] = curve_axis[i].evaluate(frame)

        anim_bone = GBoneAnimation(b_bone.name)

        # bake frames
        # TODO bake for non-linear only
        if (end_frame - start_frame > 0):
            for frame in range(start_frame, end_frame + 1):

                loc = Vector([0.0, 0.0, 0.0])
                if (len(pos_curves) == 3):
                    bake(frame, pos_curves, loc)

                sca = Vector([1.0, 1.0, 1.0])
                if (len(scale_curves) == 3):
                    bake(frame, scale_curves, sca)

                rot = Quaternion([1.0, 0.0, 0.0, 0.0])
                if (len(quat_curves) == 4):
                    bake(frame, quat_curves, rot)
                elif(len(euler_curves) == 3):
                    euler = Euler()
                    bake(frame, euler_curves, euler)
                    rot = euler.to_quaternion()

                trans = Matrix.LocRotScale(loc, rot, sca)
                rest = b_bone.matrix_local

                if (b_bone.parent):
                    # relative to parent
                    rest = b_bone.parent.matrix_local.inverted() @ b_bone.matrix_local

                pose: Matrix = rest @ trans

                millis = (1.0 / self.fps) * 1000 * frame
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


    def evaluate(self, obj: bpy.types.Object, apply_modifiers: bool) -> typing.Tuple[bpy.types.Object, bpy.types.Mesh]:
        """returns temporal trinaluated mesh with applied modifiers"""

        if (apply_modifiers):
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            self.tringalute(obj_eval.data)
            return (obj_eval, obj_eval.data)

        mesh = obj.to_mesh()
        self.tringalute(mesh)
        return (obj, mesh)

    def generate(self, objects: list[bpy.types.Object]) -> G3D:
        print(f'generate: objects count: {len(objects)}')
        
        g3d = G3D()

        for obj in objects:

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