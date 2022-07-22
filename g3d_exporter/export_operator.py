# <pep8 compliant>
import logging
import time
import traceback

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import BoolProperty, IntProperty, EnumProperty
from bpy.types import Operator

import shutil

from g3d_exporter import builder
from g3d_exporter.builder import ModelOptions
from g3d_exporter.model import G3dModel, G3dModelInfo
from g3d_exporter.common import *
from g3d_exporter import encoder

log = logging.getLogger(__name__)


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

    descriptor: BoolProperty(
        name="Descriptor",
        description="Create human-readable model description (.yaml)",
        default=False,
    )

    use_normal: BoolProperty(
        name="Normal",
        description="Include vertex normal attribute",
        default=True,
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
        description="Export shapekeys",
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
        description="Max bones per single nodepart.\nThe recommended value is vertex_bones * 3",
        default=12,
    )

    add_bone_tip: BoolProperty(
        name="Bone tip",
        description="Add extra bone with name '_end' to the last bone",
        default=True,
    )

    deform_bones_only: BoolProperty(
        name="Deform bones only",
        description="",
        default=True,
    )

    use_actions: BoolProperty(
        name="Actions",
        description="Export actions as animation",
        default=True,
    )

    use_material: BoolProperty(
        name="Export material",
        description="Export material parameters",
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
        default='AUTO',
        items=(
            ('AUTO', 'Auto', 'The Wired objects will be treated as a Line strip, all the others are Triangles'),
            ('TRIANGLES', 'Triangles', ''),
            ('LINES', 'Lines', ''),
            ('POINTS', 'Points', ''),
            ( 'TRIANGLE_STRIP', 'Triangle strip', ''),
            ( 'LINE_STRIP', 'Line strip', ''))
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
        box.label(text="Mesh")
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

        # will be replaced with alternative implementation
        # box.row().prop(operator, "use_shapekeys")
        box.row().prop(operator, "primitive_type")

        # material
        box = layout.box()
        box.label(text="Material")
        box.row().prop(operator, "use_material")

        row = box.row()
        row.enabled = self.use_material
        row.prop(operator, "copy_textures")
        row = box.row()
        row.enabled = self.copy_textures
        row.prop(operator, "copy_texture_strategy")

        # armature
        box = layout.box()
        box.label(text="Armature")
        box.row().prop(operator, "use_armature")
        row = box.row()
        row.enabled = self.use_armature
        row.prop(operator, "deform_bones_only")
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
        box.label(text="Armature")
        box.row().prop(operator, "use_actions")

        row = box.row()
        row.enabled = self.use_actions
        row.prop(operator, "fps")

    def execute(self, context):
        """called by blender"""

        start = time.process_time()
        try:
            opt = self._build_options()

            builder.b_log = self.report
            model = builder.build(opt)

            out = Path(self.filepath)

            if self.copy_textures:
                self._copy_textures(out.parent, model)

            writepath = self.export_g3d(out, model)

            if self.descriptor:
                self._write_description(model, writepath.with_suffix(".yaml"))

            duration = time.process_time() - start
            self.report({'INFO'}, "Export {:s} ({:.2f} sec)".format(str(writepath), duration))

        except G3dError as e:
            self.report({'ERROR'}, str(e))
            log.exception(str(e))

        return {'FINISHED'}

    def _write_description(self, g3d: G3dModel, path):
        info = G3dModelInfo()
        info.update(g3d)
        write(encoder.encode_info(info), path)

    def _build_options(self) -> ModelOptions:
        opt = ModelOptions()
        opt.selected_only = self.selected_only
        opt.y_up = self.y_up
        opt.use_normal = self.use_normal
        opt.use_color = self.use_color
        opt.use_material = self.use_material
        opt.packed_color = self.packed_color
        opt.use_uv = self.use_uv
        opt.use_tangent = self.use_tangent
        opt.use_binormal = self.use_binormal
        opt.flip_uv = self.flip_uv
        opt.use_armature = self.use_armature
        opt.max_bones_per_vertex = self.max_bones_per_vertex
        opt.max_bones_per_nodepart = self.max_bones_per_nodepart
        opt.use_shapekeys = self.use_shapekeys
        opt.deform_bones_only = self.deform_bones_only
        opt.use_actions = self.use_actions
        opt.add_bone_tip = self.add_bone_tip
        opt.apply_modifiers = self.apply_modifiers
        opt.fps = self.fps
        opt.primitive_type = self.primitive_type
        return opt

    def export_g3d(self, out: Path, model: G3dModel) -> Path:
        raise ValueError("not implemented")

    def _copy_textures(self, source_dir: Path, model: G3dModel):
        """Copy or unpack textures to 'textures' sub folder and update model paths"""
        dst_dir = source_dir / "textures"
        dst_dir.mkdir(exist_ok=True)

        for mat in model.materials:
            for tex in mat.textures:
                img = tex.image
                dst = dst_dir / tex.filename
                tex.filename = f"textures/{tex.filename}"

                if self.copy_texture_strategy == 'RESPECT' and dst.exists():
                    continue

                log.debug("copy texture %s to %s", tex.id, dst)

                try:
                    if img.packed_file is None:
                        shutil.copyfile(img.filepath_from_user(), dst)
                    else:
                        with open(dst, 'wb') as f:
                            f.write(img.packed_file.data)
                except FileNotFoundError as e:
                    raise G3dError(f"Cannot copy texture: {e}")


class G3djExportOperator(Operator, BaseG3dExportOperator):
    bl_idname = "export_scene.g3dj"
    bl_label = "LibGDX (.g3dj)"
    filename_ext = ".g3dj"
    bl_options = {'PRESET'}

    def export_g3d(self, filepath: Path, model: G3dModel) -> Path:
        data = encoder.encode_json(model)
        return write(data, filepath.with_suffix('.g3dj'), 'w')


class G3dbExportOperator(Operator, BaseG3dExportOperator):
    bl_idname = "export_scene.g3db"
    bl_label = "LibGDX (.g3db)"
    filename_ext = ".g3db"
    bl_options = {'PRESET'}

    def export_g3d(self, filepath: Path, model: G3dModel) -> Path:
        data = encoder.encode_binary(model)
        return write(data, filepath.with_suffix('.g3db'), 'wb')


def menu_func_export(self, context):
    self.layout.operator(G3djExportOperator.bl_idname, text="G3D (.g3dj)")
    self.layout.operator(G3dbExportOperator.bl_idname, text="G3D (.g3db)")


def register():
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
