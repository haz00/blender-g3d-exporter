# <pep8 compliant>

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator

from pathlib import Path
from typing import Any, List
import shutil

from .model import G3dModel, GShape
from .generator import G3dBuilder
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
        name="Normal",
        description="Include vertex normal attribute",
        default=False,
    )

    use_color: BoolProperty(
        name="Color",
        description="Include vertex color attribute. The Active Render slot in Vertex Colors will be used",
        default=False,
    )

    packed_color: BoolProperty(
        name="Packed color",
        description="Pack RGBA floats into single int",
        default=True,
    )

    use_uv: BoolProperty(
        name="UV",
        description="The Active Render slot in UV Maps will be used",
        default=True,
    )

    flip_uv: BoolProperty(
        name="Flip UV",
        description="Invert verical uv coordinate",
        default=True,
    )

    use_tangent: BoolProperty(
        name="Tangent",
        description="Include vertex tangent attribute",
        default=False,
    )

    use_binormal: BoolProperty(
        name="Bi-normal",
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
        name="Vertex bones",
        description="Max bones per single vertex",
        default=4,
    )

    max_bones_per_nodepart: IntProperty(
        name="Nodepart bones",
        description="Max bones per single nodepart. The recomended value is vertex_bones * 3",
        default=12,
    )

    add_bone_tip: BoolProperty(
        name="Bone tip",
        description="Add extra bone with name '_end' to the last bone",
        default=True,
    )

    use_actions: BoolProperty(
        name="Actions",
        description="Export actions as animation",
        default=True,
    )

    copy_textures: BoolProperty(
        name="Copy textures",
        description="Copy or unpack associated textures to textures/ subfolder and update model path to it",
        default=False,
    )

    copy_texture_strategy: EnumProperty(
        name="Strategy",
        default='RESPECT',
        items=(
            ('RESPECT', 'Respect', 'Keep file if exists (update paths only), create if not'),
            ('OVERWRITE', 'Overwrite', 'Always overwirte file'))
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
    

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        sfile = context.space_data
        operator = sfile.active_operator

        layout.row().prop(operator, "selected_only")
        layout.row().prop(operator, "apply_modifiers")
        layout.row().prop(operator, "y_up")

        # mesh attributes
        box = layout.box()
        box.label(text = "Mesh")
        box.row().prop(operator, "use_normal")

        row = box.row()
        row.prop(operator, "use_color")

        sub = row.row()
        sub.enabled = self.use_color
        sub.prop(operator, "packed_color", text="", icon='UGLYPACKAGE')

        box.row().prop(operator, "use_tangent")
        box.row().prop(operator, "use_binormal")

        row = box.row()
        row.prop(operator, "use_uv")

        sub = row.row()
        sub.enabled = self.use_uv
        sub.prop(operator, "flip_uv", text="", icon='MOD_MIRROR')

        box.row().prop(operator, "use_shapekeys")
        box.row().prop(operator, "primitive_type")

        # material
        box = layout.box()
        box.label(text = "Material")
        box.row().prop(operator, "copy_textures")
        
        row = box.row()
        row.enabled = self.copy_textures
        row.prop(operator, "copy_texture_strategy")

        # armature
        box = layout.box()
        box.label(text = "Armature")
        box.row().prop(operator, "use_armature")
        row = box.row()
        row.enabled = self.use_armature
        row.prop(operator, "add_bone_tip")
        row = box.row()
        row.enabled = self.use_armature
        row.prop(operator, "max_bones_per_vertex")
        row = box.row()
        row.enabled = self.use_armature
        row.prop(operator, "max_bones_per_nodepart")

        # animation
        box = layout.box()
        box.label(text = "Armature")
        box.row().prop(operator, "use_actions")
        
        row = box.row()
        row.enabled = self.use_actions 
        row.prop(operator, "fps")


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        sfile = context.space_data
        operator = sfile.active_operator

        layout.row().prop(operator, "selected_only")
        layout.row().prop(operator, "apply_modifiers")
        layout.row().prop(operator, "y_up")

        # mesh attributes
        box = layout.box()
        box.label(text = "Mesh")
        box.row().prop(operator, "use_normal")

        row = box.row()
        row.prop(operator, "use_color")

        sub = row.row()
        sub.enabled = self.use_color
        sub.prop(operator, "packed_color", text="", icon='UGLYPACKAGE')

        box.row().prop(operator, "use_tangent")
        box.row().prop(operator, "use_binormal")

        row = box.row()
        row.prop(operator, "use_uv")

        sub = row.row()
        sub.enabled = self.use_uv
        sub.prop(operator, "flip_uv", text="", icon='MOD_MIRROR')

        box.row().prop(operator, "use_shapekeys")
        box.row().prop(operator, "primitive_type")

        # material
        box = layout.box()
        box.label(text = "Material")
        box.row().prop(operator, "copy_textures")
        
        row = box.row()
        row.enabled = self.copy_textures
        row.prop(operator, "copy_texture_strategy")

        # armature
        box = layout.box()
        box.label(text = "Armature")
        box.row().prop(operator, "use_armature")
        row = box.row()
        row.enabled = self.use_armature
        row.prop(operator, "max_bones_per_vertex")
        row = box.row()
        row.enabled = self.use_armature
        row.prop(operator, "add_bone_tip")

        # animation
        box = layout.box()
        box.label(text = "Animation")
        box.row().prop(operator, "use_actions")
        
        row = box.row()
        row.enabled = self.use_actions 
        row.prop(operator, "fps")


    def execute(self, context):
        """called by blender"""

        gen = G3dBuilder()
        gen.y_up = self.y_up
        gen.use_normal = self.use_normal
        gen.use_color = self.use_color
        gen.packed_color = self.packed_color
        gen.use_uv = self.use_uv
        gen.use_tangent = self.use_tangent
        gen.use_binormal = self.use_binormal
        gen.flip_uv = self.flip_uv
        gen.use_armature = self.use_armature
        gen.max_bones_per_vertex = self.max_bones_per_vertex
        gen.max_bones_per_nodepart = self.max_bones_per_nodepart
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

        if self.copy_textures:
            self._copy_textures(out.parent, model)

        self.export_g3d(out, model)

        if self.use_shapekeys:
            self.export_shapekeys(out, model.shapes)

        return {'FINISHED'}


    def _write(self, data, file: Path, flags='w'):
        with open(file, flags) as f:
            f.write(data)
            print('write', file.absolute())


    def _copy_textures(self, source_dir: Path, model: G3dModel):
        """Copy or unpack textures to textures subfolder and update model paths"""
        dst_dir =  source_dir / "textures"
        dst_dir.mkdir(exist_ok=True)

        for mat in model.materials.values():
            for tex in mat.textures:
                img = tex.source 
                dst = dst_dir / tex.filename
                tex.filename = f"textures/{tex.filename}"

                if self.copy_texture_strategy == 'RESPECT' and dst.exists():
                    continue

                print(f"copy texture {tex.id} to {dst}")

                if img.packed_file == None:
                    shutil.copyfile(img.filepath_from_user(), dst)
                else:
                    with open(dst, 'wb') as f:
                        f.write(img.packed_file.data)
                

class G3djExportOperator(Operator, BaseG3dExportOperator):
    bl_idname = "export_scene.g3dj"
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
    bl_idname = "export_scene.g3db"
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
    self.layout.operator(G3djExportOperator.bl_idname, text="G3D (.g3dj)")
    self.layout.operator(G3dbExportOperator.bl_idname, text="G3D (.g3db)")



def register():
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
