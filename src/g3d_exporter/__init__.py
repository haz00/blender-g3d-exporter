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
    importlib.reload(common)
    importlib.reload(g3db_encoder)
    importlib.reload(g3dj_encoder)
    importlib.reload(generator)
    importlib.reload(model)
    importlib.reload(export_operator)
else:
    import bpy
    from . import common
    from . import g3db_encoder
    from . import g3dj_encoder
    from . import generator
    from . import model
    from . import export_operator

classes = [
    export_operator.G3djExportOperator,
    export_operator.G3dbExportOperator,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    export_operator.register_menu()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    export_operator.unregister_menu()


if __name__ == "__main__":
    register()
