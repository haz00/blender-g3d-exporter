# <pep8 compliant>

bl_info = {
    "name": "LibGDX G3D Exporter",
    "description": "Export scene to LibGDX compatible format",
    "author": "haz00",
    "version": (0, 3),
    "blender": (2, 93, 0),
    "location": "File > Export",
    "category": "Import-Export",
    'support': 'COMMUNITY',
    "tracker_url": "https://github.com/haz00/blender-g3d-exporter/issues",
    "wiki_url": "https://github.com/haz00/blender-g3d-exporter",
}

if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(domain)
    importlib.reload(g3dj_encoder)
    importlib.reload(generator)
    importlib.reload(export_operator)
else:
    import bpy
    import sys
    import os

    # add addon directory to classpath
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    import utils
    import domain
    import g3dj_encoder
    import generator
    import export_operator


classes = [
    export_operator.G3djExportOperator
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    export_operator.add_menu()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    export_operator.remove_menu()
