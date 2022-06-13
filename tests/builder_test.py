import unittest

import bpy

from g3d_exporter import builder
from g3d_exporter.builder import *
from g3d_exporter.model import *
from tests.base import BaseTest
from tests.common import *


class G3dBuilderTest(BaseTest):

    def test_flags(self):
        a = tuple([VertexFlag("A", 3), VertexFlag("B", 3)])
        b = tuple([VertexFlag("A", 3), VertexFlag("B", 3)])
        c = tuple([VertexFlag("B", 3), VertexFlag("A", 3)])

        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    # @unittest.skip("skip")
    def test_meshkey(self):
        a = bpy.data.objects.new("a", bpy.data.meshes.new("a"))
        b = bpy.data.objects.new("b", bpy.data.meshes.new("b"))
        b2 = bpy.data.objects.new("b", b.data)

        a_mesh = evaluate(a, True)[1]
        b_mesh = evaluate(b, True)[1]
        b2_mesh = evaluate(b2, True)[1]

        self.assertNotEqual(hash(a_mesh), hash(b_mesh))
        self.assertEqual(hash(b2_mesh), hash(b_mesh))

    # @unittest.skip("skip")
    def test_mergekey(self):
        a = MeshNodeDataBuilder._compute_gmesh_key(tuple([VertexFlag("a", 2)]), None)
        b = MeshNodeDataBuilder._compute_gmesh_key(tuple([VertexFlag("a", 2)]), None)
        c = MeshNodeDataBuilder._compute_gmesh_key(tuple([VertexFlag("a", 4)]), None)

        self.assertEqual(hash(a), hash(b))
        self.assertEqual(a, b)

        self.assertNotEqual(a, c)
        self.assertNotEqual(hash(a), hash(c))

    # @unittest.skip("skip")
    def test_material(self):
        mat = bpy.data.materials.new("test_material")
        # TODO construct material by code

        builder = MaterialBuilder(G3Data(), ModelOptions())
        gmat = builder.build(mat)

        self.assertEqual(gmat.id, "test_material")
        self.assertEqual(len(gmat.textures), 0)
        self.assertEqual(len(gmat.attributes), 0)

    # @unittest.skip("skip")
    def test_parent(self):
        """
        Outliner:
        obj1
            obj2
        """

        obj1 = add_triangle("obj1")
        obj2 = add_triangle("obj2", mat=obj1.data.materials[0])
        obj2.parent = obj1

        opt = ModelOptions()
        opt.selected_only = True

        mod = builder.build(opt)
        dump_model(self.test_parent.__name__, mod)

        self.assertEqual(len(mod.meshes), 1)
        self.assertEqual(mod.meshes[0].vertex_count(), 3)
        self.assertEqual(len(mod.meshes[0].parts), 2)

        self.assertEqual(len(mod.nodes), 1)
        self.assertEqual(len(mod.nodes[0].children), 1)

    # @unittest.skip("skip")
    def test_linked(self):
        """
        Outliner:
        obj1
        obj2
        """

        obj1 = add_triangle("obj1")
        obj2 = add_triangle("obj2", mesh=obj1.data, mat=obj1.data.materials[0])

        opt = ModelOptions()
        opt.selected_only = True

        mod = builder.build(opt)
        dump_model(self.test_linked.__name__, mod)

        self.assertEqual(len(mod.meshes), 1)
        self.assertEqual(mod.meshes[0].vertex_count(), 3)
        self.assertEqual(len(mod.meshes[0].parts), 1)

        self.assertEqual(len(mod.nodes), 2)

    # @unittest.skip("skip")
    def test_linked_with_modifiers(self):
        obj1 = add_triangle("obj1")
        obj2 = add_triangle("obj2", mesh=obj1.data, mat=obj1.data.materials[0])
        obj2.modifiers.new('solidify', 'SOLIDIFY')

        opt = ModelOptions()
        opt.selected_only = True

        mod = builder.build(opt)
        dump_model(self.test_linked_with_modifiers.__name__, mod)

        self.assertEqual(len(mod.meshes), 1)
        self.assertEqual(mod.meshes[0].vertex_count(), 9)
        self.assertEqual(len(mod.meshes[0].parts), 2)

        self.assertEqual(len(mod.nodes), 2)

    # @unittest.skip("skip")
    def test_collection(self):
        """
        Outliner:
        test_collection /
            obj2
                obj3
        obj1
        """
        collection = add_collection(self.test_collection.__name__)

        obj1 = add_triangle("obj1")

        obj2 = add_triangle("obj2", mat=obj1.data.materials[0])
        move_to_collection(obj2, collection.name)

        obj3 = add_triangle("obj3", mat=obj1.data.materials[0])
        obj3.parent = obj2
        move_to_collection(obj3, collection.name)

        opt = ModelOptions()
        opt.selected_only = True

        mod = builder.build(opt)
        dump_model(self.test_collection.__name__, mod)

        self.assertEqual(len(mod.meshes), 1)
        self.assertEqual(mod.meshes[0].vertex_count(), 3)
        self.assertEqual(len(mod.meshes[0].parts), 3)

        self.assertEqual(len(mod.nodes), 2)

    # @unittest.skip("skip")
    def test_collection_instance(self):
        """
        Outliner:
        test_collection_instance/ : excluded
            obj1
        test_collection_instance
        """
        collection = add_collection(self.test_collection_instance.__name__)
        bpy.context.view_layer.layer_collection.children[collection.name].exclude = True

        obj1 = add_triangle("obj1")
        move_to_collection(obj1, collection.name)

        empty1 = add_collection_instance(collection.name)

        opt = ModelOptions()
        opt.selected_only = True

        mod = builder.build(opt)
        dump_model(self.test_collection_instance.__name__, mod)

        self.assertEqual(len(mod.meshes), 1)
        self.assertEqual(mod.meshes[0].vertex_count(), 3)
        self.assertEqual(len(mod.meshes[0].parts), 1)

        self.assertEqual(len(mod.nodes), 1)
        self.assertEqual(len(mod.nodes[0].children), 1)

    # @unittest.skip("skip")
    def test_armature_node(self):
        """
        Outliner:
        armature
            Bone
                Bone.001

        Nodes:
        armature
            Bone
                Bone.001
                    Bone.001_end
        """

        obj1 = add_armature("armature")

        opt = ModelOptions()
        opt.selected_only = True

        mod = builder.build(opt)
        dump_model(self.test_armature_node.__name__, mod)

        self.assertEqual(len(mod.meshes), 0)
        self.assertEqual(len(mod.nodes), 1)

        expect_child = GNode("Bone.001_end")
        expect_parent = GNode("Bone.001")
        expect_parent.children.append(expect_child)

        expect_child = expect_parent
        expect_parent = GNode("Bone")
        expect_parent.children.append(expect_child)

        expect_child = expect_parent
        expect_parent = GNode(obj1.name)
        expect_parent.children.append(expect_child)

        self._check_node_chain(mod.nodes[0], expect_parent)

    # @unittest.skip("skip")
    def test_skinned_mesh_split_nodepart(self):
        """
        Outliner:
        armature
            Bone
                Bone.001
                    x10
            obj1
        """
        opt = ModelOptions()
        opt.selected_only = True
        opt.use_normal = False
        opt.use_tangent = False
        opt.use_binormal = False
        opt.use_uv = False
        opt.bones_per_vertex = 1
        opt.max_bones_per_nodepart = opt.bones_per_vertex * 3

        obj_arm = add_armature("armature", bones_count=10)

        obj1 = add_triangle("obj1", count=2)
        make_skinned(obj_arm, obj1)
        obj1.vertex_groups['Bone'].add([0], 0.5, 'REPLACE')
        obj1.vertex_groups['Bone.001'].add([1], 0.5, 'REPLACE')
        obj1.vertex_groups['Bone.002'].add([2], 0.5, 'REPLACE')
        obj1.vertex_groups['Bone.003'].add([3], 0.5, 'REPLACE')
        obj1.vertex_groups['Bone.004'].add([4], 0.5, 'REPLACE')
        obj1.vertex_groups['Bone.005'].add([5], 0.5, 'REPLACE')

        mod = builder.build(opt)
        dump_model(self.test_skinned_mesh_split_nodepart.__name__, mod)

        self.assertEqual(len(mod.meshes), 1)
        self.assertEqual(len(mod.meshes[0].parts), 2)
        self.assertEqual(len(mod.meshes[0].vertices), 6 * 5)

        self.assertEqual(len(mod.nodes), 2)
        self.assertEqual(mod.nodes[0].id, 'obj1')
        self.assertEqual(len(mod.nodes[0].parts[0].bones), opt.max_bones_per_nodepart)
        self.assertEqual(len(mod.nodes[0].parts[1].bones), opt.max_bones_per_nodepart)

        # BLENDWEIGHT0
        self._check_blendweight(mod.meshes[0].vertices, 3, 0, 1)
        self._check_blendweight(mod.meshes[0].vertices, 3 + 5, 1, 1)
        self._check_blendweight(mod.meshes[0].vertices, 3 + 10, 2, 1)

    # @unittest.skip("skip")
    def test_no_blendweights_in_skinned_mesh(self):
        """
        Outliner:
        armature
            Bone
                Bone.001
            obj1
        """

        obj_arm = add_armature("armature")
        obj1 = add_triangle("obj1")

        make_skinned(obj_arm, obj1)

        slots = obj1.vertex_groups
        builder = BlendweightAttributeBuilder(slots, obj_arm, 4, 12)

        opt = ModelOptions()
        info = VertexInfo(obj1.data.vertices[0], obj1.data.loops[0], obj1, obj1.data, opt)
        info.bones = dict()

        data: List[float] = list()
        nodepart = NodePartBuilder(None, None)
        self.assertRaises(G3dError, builder.build, info, data, nodepart)

    # @unittest.skip("skip")
    def test_linear_animation(self):
        """
        Outliner:
        armature
            Bone
                Bone.001
        """

        obj1 = add_armature("armature")

        action1 = bpy.data.actions.new("action1")

        flocx = action1.fcurves.new('pose.bones["Bone"].location', index=0, action_group="Bone")
        k = flocx.keyframe_points.insert(10, 0)
        k.interpolation = 'LINEAR'
        k = flocx.keyframe_points.insert(40, 3)
        k.interpolation = 'LINEAR'

        fscax = action1.fcurves.new('pose.bones["Bone.001"].scale', index=0, action_group="Bone.001")
        k = fscax.keyframe_points.insert(10, 1)
        k.interpolation = 'LINEAR'
        k = fscax.keyframe_points.insert(40, 3)
        k.interpolation = 'LINEAR'

        opt = ModelOptions()
        opt.selected_only = True
        opt.fps = 30

        mod = builder.build(opt)
        dump_model(self.test_linear_animation.__name__, mod)

        self.assertEqual(len(mod.animations), 1)
        self.assertEqual(mod.animations[0].id, f"{obj1.name}|{action1.name}")
        self.assertEqual(len(mod.animations[0].bones), 2)
        self.assertEqual(len(mod.animations[0].bones[0].keyframes), 2)
        self.assertEqual(len(mod.animations[0].bones[1].keyframes), 2)
        self.assertEqual(mod.animations[0].bones[0].keyframes[0].keytime, 0.0)
        self.assertAlmostEqual(mod.animations[0].bones[0].keyframes[1].keytime, 1000, 3)

    # @unittest.skip("skip")
    def test_nonlinear_animation(self):
        """
        Outliner:
        armature
            Bone
                Bone.001
        """

        obj1 = add_armature("armature")

        action1 = bpy.data.actions.new("action1")

        flocx = action1.fcurves.new('pose.bones["Bone"].location', index=0, action_group="Bone")
        flocx.keyframe_points.insert(10, 0)
        flocx.keyframe_points.insert(40, 3)

        total_frames = 40 - 10 + 1
        opt = ModelOptions()
        opt.selected_only = True
        opt.fps = 30

        mod = builder.build(opt)
        dump_model(self.test_nonlinear_animation.__name__, mod)

        self.assertEqual(len(mod.animations), 1)
        self.assertEqual(mod.animations[0].id, f"{obj1.name}|{action1.name}")
        self.assertEqual(len(mod.animations[0].bones), 1)
        self.assertAlmostEqual(len(mod.animations[0].bones[0].keyframes), total_frames)
        self.assertEqual(mod.animations[0].bones[0].keyframes[0].keytime, 0)
        self.assertAlmostEqual(mod.animations[0].bones[0].keyframes[-1].keytime, 1000, 3)

    # @unittest.skip("skip")
    def test_shapekeys(self):
        """
        Outliner:
        obj1
        obj2
        """

        obj1 = add_triangle("obj1")
        k = obj1.shape_key_add(name="Basis")
        k = obj1.shape_key_add(name="Key")
        for i in range(len(obj1.data.vertices)):
            k.data[i].co.x = 20
            k.data[i].co.y = 10
            k.data[i].co.z = -10

        obj2 = add_triangle("obj2")
        k = obj2.shape_key_add(name="Basis")

        opt = ModelOptions()
        opt.selected_only = True

        mod = builder.build(opt)
        dump_model(self.test_shapekeys.__name__, mod)

        self.assertEqual(len(mod.meshes), 2)
        self.assertEqual(len(mod.shapes), 2)
        self.assertEqual(len(mod.shapes[0].keys), 2)
        self.assertEqual(len(mod.shapes[1].keys), 1)

        self.assertEqual(mod.shapes[0].keys[1].name, "Key")
        self.assertEqual(len(mod.shapes[0].keys[1].positions), 3 * 3)
        self.assertAlmostEqual(mod.shapes[0].keys[1].positions[0], 20.000, 3)
        self.assertAlmostEqual(mod.shapes[0].keys[1].positions[1], 10.000, 3)
        self.assertAlmostEqual(mod.shapes[0].keys[1].positions[2], -10.000, 3)

    def _check_node_chain(self, test: GNode, expect: GNode):
        self.assertEqual(test.id, expect.id)
        self.assertEqual(len(test.children), len(test.children))

        for i in range(len(test.children)):
            self._check_node_chain(test.children[i], expect.children[i])

    def _check_blendweight(self, vertices: List[float], idx: int, expect_idx: float, expect_w: float):
        self.assertAlmostEqual(vertices[idx], expect_idx)
        self.assertAlmostEqual(vertices[idx + 1], expect_w, 3)


class MeshNodeDataBuilderTest(BaseTest):

    # @unittest.skip("skip")
    def test_analyze_attributes(self):
        obj = add_triangle("test_analyze_attributes")

        opt = ModelOptions()

        meshdata_builder = MeshNodeDataBuilder(G3Data(), opt)
        attrs = meshdata_builder._analyze_mesh(obj, obj.data, None)

        expect_flags = (
            VertexFlag("POSITION", 3),
            VertexFlag("NORMAL", 3),
            VertexFlag("TANGENT", 3),
            VertexFlag("BINORMAL", 3),
            VertexFlag("TEXCOORD0", 2),
        )
        self.assertEqual(attrs.flags(), expect_flags)


class BlendweightAttributeBuilderTest(BaseTest):
    obj1: bpy.types.Object
    obj_arm: bpy.types.Object

    def setUp(self):
        super().setUp()

        self.obj_arm = add_armature("armature", bones_count=10)

        self.obj1 = add_triangle("obj1")
        make_skinned(self.obj_arm, self.obj1)
        self.obj1.vertex_groups['Bone'].add([0], 1, 'REPLACE')
        self.obj1.vertex_groups['Bone.001'].add([1, 2], 1, 'REPLACE')

        self.obj1.vertex_groups.new(name="not a bone")
        self.obj1.vertex_groups['not a bone'].add([0, 1, 2], 1, 'REPLACE')

    # @unittest.skip("skip")
    def test_optimal_length(self):
        slots = self.obj1.vertex_groups
        bones = self.obj_arm.data.bones

        builder = BlendweightAttributeBuilder(slots, bones, 0, 0)

        self.obj1.vertex_groups['Bone'].add([0, 1, 2], 0, 'REPLACE')
        self.obj1.vertex_groups['Bone.001'].add([0, 1, 2], 0, 'REPLACE')
        builder.set_optimal_length(self.obj1.data, 4)
        self.assertEqual(builder.length, 0)

        self.obj1.vertex_groups['Bone'].add([0], 1, 'REPLACE')
        self.obj1.vertex_groups['Bone.001'].add([1], 1, 'REPLACE')
        builder.set_optimal_length(self.obj1.data, 4)
        self.assertEqual(builder.length, 2)

    # @unittest.skip("skip")
    def test_setup_vertex(self):
        opt = ModelOptions()
        slots = self.obj1.vertex_groups
        bones = self.obj_arm.data.bones

        builder = BlendweightAttributeBuilder(slots, bones, 3, opt.max_bones_per_nodepart)

        v0 = VertexInfo(self.obj1.data.vertices[0], self.obj1.data.loops[0], self.obj1, self.obj1.data, opt)
        builder.setup_vertex(v0)

        self.assertEqual(len(v0.vert.groups), 2)
        self.assertIn('Bone', builder._bones)
        self.assertNotIn('Bone.001', builder._bones)

        v1 = VertexInfo(self.obj1.data.vertices[1], self.obj1.data.loops[0], self.obj1, self.obj1.data, opt)

        builder.setup_vertex(v1)

        self.assertEqual(len(v1.vert.groups), 2)
        self.assertIn('Bone', builder._bones)
        self.assertIn('Bone.001', builder._bones)

    # @unittest.skip("skip")
    def test_build(self):
        opt = ModelOptions()

        slots = self.obj1.vertex_groups
        bones = self.obj_arm.data.bones

        builder = BlendweightAttributeBuilder(slots, bones, 2, opt.max_bones_per_nodepart)

        data = list()
        nodepart = NodePartBuilder(None, None)

        vert = self.obj1.data.vertices[0]
        v0 = VertexInfo(vert, self.obj1.data.loops[0], self.obj1, self.obj1.data, opt)
        v0.bones = dict()
        v0.bones['Bone'] = VertexBoneGroup(bones['Bone'], vert.groups[0])

        builder.build(v0, data, nodepart)

        self.assertEqual(len(data), 4)
        self.assertAlmostEqual(data[1], 1)
        self.assertAlmostEqual(data[3], 0)

        self.assertEqual(len(nodepart.bones), 1)
        self.assertIn('Bone', nodepart.bones)

    # @unittest.skip("skip")
    def test_filter_nodepart(self):
        opt = ModelOptions()
        opt.max_bones_per_nodepart = 2

        slots = self.obj1.vertex_groups
        bones = self.obj_arm.data.bones

        builder = BlendweightAttributeBuilder(slots, bones, 0, opt.max_bones_per_nodepart)

        nodepart = NodePartBuilder(None, None)
        nodepart.bones = dict()

        builder._bones = dict()
        self.assertTrue(builder.filter_nodepart(nodepart))

        builder._bones = dict()
        builder._bones['Bone'] = bones['Bone']
        builder._bones['Bone.001'] = bones['Bone.001']
        builder._bones['Bone.002'] = bones['Bone.002']
        self.assertFalse(builder.filter_nodepart(nodepart))

