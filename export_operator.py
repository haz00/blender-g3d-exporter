# <pep8 compliant>

from pathlib import Path
from typing import Any, List
import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator
from domain import G3D, GShape
import g3dj_encoder
import g3db_encoder
from generator import G3dGenerator


class G3dExportOperator(Operator, ExportHelper):
    bl_idname = "g3dj_export_operator.export"
    bl_label = "LibGDX (.g3dj)"

    filename_ext = ".g3dj"

    selected_only: BoolProperty(
        name="Selected Only",
        description="",
        default=False,
    )

    binary: BoolProperty(
        name="Binary",
        description="Export to .g3db",
        default=True,
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

        if self.selected_only:
            objects = bpy.context.selected_objects 
        else:
            objects = list(bpy.data.objects)

        g3d = gen.generate(objects)
        out = Path(self.filepath)

        export_g3d(out, g3d, self.binary)

        if self.use_shapekeys:
            export_shapekeys(out, g3d.shapes, self.binary)

        return {'FINISHED'}


def export_g3d(filepath: Path, g3d: G3D, binary=True):
    if (binary):
        data = g3db_encoder.encode(g3d)
        _write(data, filepath.with_suffix('.g3db'), 'wb')
    else:
        data = g3dj_encoder.encode(g3d)
        _write(data, filepath.with_suffix('.g3dj'), 'w')


def export_shapekeys(filepath: Path, shapes: List[GShape], binary=True):
    # TODO binary too
    data = g3dj_encoder.encode({"shapes": shapes})
    _write(data, filepath.with_suffix(".shapes"), 'w')


def _write(data, file: Path, flags='w'):
    with open(file, flags) as f:
        f.write(data)
        print('write', file.absolute())


def menu_func_export(self, context):
    self.layout.operator(G3dExportOperator.bl_idname)


def add_menu():
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def remove_menu():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
