from pathlib import Path
import logging

import bpy

from g3d_exporter import encoder
from g3d_exporter.common import write
from g3d_exporter.model import G3dModel, GModelShape

log = logging.getLogger(__name__)


def deselect_all():
    bpy.ops.object.select_all(action='DESELECT')


def dump_model(name: str, model: G3dModel):
    out_dir = Path(__file__).parent / f"build/{bpy.app.version_string}"
    out_dir.mkdir(exist_ok=True, parents=True)

    formatted = encoder.encode_json(model)

    out_file = out_dir / f"{name}.g3dj"
    write(formatted, out_file)

    formatted = encoder.encode_json(GModelShape(name, model.shapes))
    out_file = out_dir / f"{name}.shape"
    write(formatted, out_file)


def add_triangle(name, mesh=None, mat=None, select=True, count=1) -> bpy.types.Object:
    if not mesh:
        verts = list()
        edges = list()
        faces = list()

        for i in range(count):
            i3 = i * 3
            verts.extend([(-1 - i, -1, 0), (1 - i, -1, 0), (-i, 1, 0)])
            edges.extend([(i3, i3 + 1), (i3 + 1, i3 + 2), (i3 + 2, i3)])
            faces.extend([(i3, i3 + 1, i3 + 2)])

        mesh = bpy.data.meshes.new(name + '_mesh')
        mesh.from_pydata(verts, edges, faces)

    obj = bpy.data.objects.new(name, mesh)

    if not mat:
        mat = bpy.data.materials.new(name + '_mat')

    obj.data.materials.append(mat)
    obj.data.uv_layers.new()

    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(select)
    log.debug(f"add object {name}/{mesh.name}/{mat.name}/select {select}/{obj.users_collection}")
    return obj


def add_collection(name: str, parent_name: str = None) -> bpy.types.Collection:
    col = bpy.data.collections.new(name)

    if parent_name:
        bpy.data.collections[name].children.link(col)
    else:
        bpy.context.scene.collection.children.link(col)
        parent_name = bpy.context.scene.collection.name

    log.debug(f"add collection {col.name} to {parent_name}")
    return col


def add_collection_instance(name: str, select=True) -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    empty.instance_collection = bpy.data.collections[name]
    empty.instance_type = 'COLLECTION'
    bpy.context.scene.collection.objects.link(empty)
    empty.select_set(select)

    log.debug(f"add collection instance {empty.name}/select {select}/{empty.users_collection}")
    return empty


def add_armature(name: str, select=True, bones_count=2) -> bpy.types.Object:
    """creates armature with chained bones in the root collection"""
    bpy.ops.object.armature_add()

    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name

    bpy.ops.object.mode_set(mode='EDIT')

    b1 = obj.data.edit_bones['Bone']

    for i in range(bones_count - 1):
        b2 = obj.data.edit_bones.new('Bone')
        b2.tail = (0.0, 0.0, 2.0 * (i + 1))
        b2.parent = b1
        b2.use_connect = True
        b1 = b2

    bpy.ops.object.mode_set(mode='OBJECT')

    move_to_collection(obj)
    obj.select_set(select)

    log.debug(f"add armature {obj.name}/{obj.data.name}/select {select}/{obj.users_collection}")
    return obj


def move_to_collection(obj: bpy.types.Object, name: str = None):
    for col in obj.users_collection:
        col.objects.unlink(obj)

    if name:
        bpy.data.collections[name].objects.link(obj)
    else:
        bpy.context.scene.collection.objects.link(obj)

    log.debug(f"move object {obj.name} to collection {obj.users_collection}")


def clear_bpy_data():
    for v in bpy.data.actions.values():
        bpy.data.actions.remove(v)

    for v in bpy.data.armatures.values():
        bpy.data.armatures.remove(v)

    for v in bpy.data.collections.values():
        bpy.data.collections.remove(v)

    for v in bpy.data.images.values():
        bpy.data.images.remove(v)

    for v in bpy.data.lights.values():
        bpy.data.lights.remove(v)

    for v in bpy.data.materials.values():
        bpy.data.materials.remove(v)

    for v in bpy.data.meshes.values():
        bpy.data.meshes.remove(v)

    for v in bpy.data.objects.values():
        bpy.data.objects.remove(v)


def make_skinned(obj_arm: bpy.types.Object, obj: bpy.types.Object, strategy='ARMATURE_NAME'):
    deselect_all()

    bpy.context.view_layer.objects.active = obj_arm
    obj.select_set(True)
    obj_arm.select_set(True)
    bpy.ops.object.parent_set(type=strategy)


def qualified_classname(o):
    return o.__module__ + '.' + o.__name__
