# <pep8 compliant>

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator

from pathlib import Path
from typing import Any, List

from .model import G3dModel, GShape
from .generator import G3dGenerator
from . import g3dj_encoder
from . import g3db_encoder


class BaseG3dExportOperator(ExportHelper):

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
        """called by blender"""

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

        if self.selected_only:
            objects = bpy.context.selected_objects
        else:
            objects = list(bpy.data.objects)

        model = gen.generate(objects)
        out = Path(self.filepath)

        self.export_g3d(out, model)

        if self.use_shapekeys:
            self.export_shapekeys(out, model.shapes)

        return {'FINISHED'}

    def _write(self, data, file: Path, flags='w'):
        with open(file, flags) as f:
            f.write(data)
            print('write', file.absolute())


class G3djExportOperator(Operator, BaseG3dExportOperator):
    bl_idname = "g3dj_export_operator.export"
    bl_label = "LibGDX (.g3dj)"
    filename_ext = ".g3dj"
    bl_options = {'PRESET'}

    def export_g3d(self, filepath: Path, model: G3dModel):
        data = g3dj_encoder.encode(model)
        self._write(data, filepath.with_suffix('.g3dj'), 'w')

    def export_shapekeys(self, filepath: Path, shapes: List[GShape]):
        data = g3dj_encoder.encode({"shapes": shapes})
        self._write(data, filepath.with_suffix(".shapes"), 'w')


class G3dbExportOperator(Operator, BaseG3dExportOperator):
    bl_idname = "g3db_export_operator.export"
    bl_label = "LibGDX (.g3db)"
    filename_ext = ".g3db"
    bl_options = {'PRESET'}

    def export_g3d(self, filepath: Path, model: G3dModel):
        data = g3db_encoder.encode(model)
        self._write(data, filepath.with_suffix('.g3db'), 'wb')

    def export_shapekeys(self, filepath: Path, shapes: List[GShape]):
        # TODO binary too
        data = g3dj_encoder.encode({"shapes": shapes})
        self._write(data, filepath.with_suffix(".shapes"), 'w')


def menu_func_export(self, context):
    self.layout.operator(G3djExportOperator.bl_idname)
    self.layout.operator(G3dbExportOperator.bl_idname)


def register_menu():
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister_menu():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
