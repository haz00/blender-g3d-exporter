# <pep8 compliant>

bl_info = {
    "name": "LibGDX G3D Exporter",
    "description": "Export scene to LibGDX compatible format",
    "author": "haz00",
    "version": (0, 7),
    "blender": (2, 93, 0),
    "location": "File > Export",
    "category": "Import-Export",
    'support': 'COMMUNITY',
    "tracker_url": "https://github.com/haz00/blender-g3d-exporter/issues",
    "wiki_url": "https://github.com/haz00/blender-g3d-exporter",
}

if "bpy" in locals():
    import importlib
    importlib.reload(g3d_exporter.common)
    importlib.reload(g3d_exporter.encoder)
    importlib.reload(g3d_exporter.builder)
    importlib.reload(g3d_exporter.model)
    importlib.reload(g3d_exporter.export_operator)
else:
    import bpy
    import g3d_exporter.common
    import g3d_exporter.encoder
    import g3d_exporter.builder
    import g3d_exporter.model
    import g3d_exporter.export_operator

classes = [
    export_operator.G3djExportOperator,
    export_operator.G3dbExportOperator,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    export_operator.register()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    export_operator.unregister()


if __name__ == "__main__":
    register()
