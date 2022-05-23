# <pep8 compliant>

import pathlib
import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator
from g3dj_encoder import G3DJsonEncoder
from generator import G3dGenerator
import utils
import json


class G3djExportOperator(Operator, ExportHelper):
    bl_idname = "g3dj_export_operator.export"
    bl_label = "Libgdx (.g3dj)"

    filename_ext = ".g3dj"

    selected_only: BoolProperty(
        name="Selected Only",
        description="",
        default=False,
    )

    y_up: BoolProperty(
        name="Y-up",
        description="Rotate ro Y-up Z-forward",
        default=True,
    )

    apply_modifiers: BoolProperty(
        name="Apply modifiers",
        description="",
        default=True,
    )

    use_normal: BoolProperty(
        name="Vertex normal",
        description="Include vertex normal attribute",
        default=False,
    )

    use_color: BoolProperty(
        name="Vertex color",
        description="Include vertex color attribute",
        default=True,
    )

    use_color_type: EnumProperty(
        name="Vertex color type",
        description="",
        default='COLOR',
        items=(
            ('COLOR', 'COLOR', 'RGBA floats'),
            ('COLORPACKED', 'COLORPACKED', 'Pack RGBA floats into single int'))
    )
    
    use_uv: BoolProperty(
        name="UV",
        description="",
        default=True,
    )

    flip_uv: BoolProperty(
        name="Flip UV",
        description="Invert verical uv coordinate",
        default=True,
    )

    use_tangent: BoolProperty(
        name="Vertex tangent",
        description="Include vertex tangent attribute",
        default=False,
    )

    use_binormal: BoolProperty(
        name="Vertex binormal",
        description="Include vertex binormal attribute",
        default=False,
    )

    use_shapekeys: BoolProperty(
        name="Shapekeys",
        description="Export shapekeys to separate .shapes file",
        default=False,
    )

    use_armature: BoolProperty(
        name="Armature",
        description="",
        default=True,
    )

    max_bones_per_vertex: IntProperty(
        name="Max bones per vertex",
        description="",
        default=4,
    )

    add_bone_tip: BoolProperty(
        name="Bone tip",
        description="Add extra bone with name _end to the last bone",
        default=True,
    )

    use_actions: BoolProperty(
        name="Animation",
        description="",
        default=True,
    )

    fps: IntProperty(
        name="FPS target",
        description="Used to bake animation",
        default=24,
    )

    primitive_type: EnumProperty(
        name="Primitive type",
        description="Used to specify the primitive type of the mesh part",
        default='TRIANGLES',
        items=(
            ('TRIANGLES', 'TRIANGLES', ''),
            ('LINES', 'LINES', ''),
            ('POINTS', 'POINTS', ''),
            ('TRIANGLE_STRIP', 'TRIANGLE_STRIP', ''),
            ('LINE_STRIP', 'LINE_STRIP', ''))
    )

    def execute(self, context):
        """calls by blender"""

        gen = G3dGenerator()
        gen.y_up = self.y_up
        gen.use_normal = self.use_normal
        gen.use_color = self.use_color
        gen.use_color_type = self.use_color_type
        gen.use_uv = self.use_uv
        gen.use_tangent = self.use_tangent
        gen.use_binormal = self.use_binormal
        gen.flip_uv = self.flip_uv
        gen.use_armature = self.use_armature
        gen.max_bones_per_vertex = self.max_bones_per_vertex
        gen.use_shapekeys = self.use_shapekeys
        gen.use_actions = self.use_actions
        gen.add_bone_tip = self.add_bone_tip
        gen.apply_modifiers = self.apply_modifiers
        gen.fps = self.fps
        gen.primitive_type = self.primitive_type

        objects = bpy.context.selected_objects if (self.selected_only) else bpy.data.objects

        do_export(pathlib.Path(self.filepath), gen, objects)

        return {'FINISHED'}


def do_export(filepath: pathlib.Path, gen: G3dGenerator, objects: list[bpy.types.Object]):
    g3d = gen.generate(objects)

    data = json.dumps(g3d.to_dict(), indent=2, cls=G3DJsonEncoder, float_round=6)
    utils.write(filepath, data)

    if (gen.use_shapekeys):
        root = dict()
        root['shapes'] = [shape.to_dict() for shape in g3d.shapes]
        data = json.dumps(root, indent=2, cls=G3DJsonEncoder, float_round=6)
        utils.write(filepath.with_suffix(".shapes"), data)


def menu_func_export(self, context):
    self.layout.operator(G3djExportOperator.bl_idname)


def add_menu():
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def remove_menu():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
