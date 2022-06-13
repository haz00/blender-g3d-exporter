import unittest

import bpy
from g3d_exporter.export_operator import G3djExportOperator
from g3d_exporter.export_operator import G3dbExportOperator
from tests.common import deselect_all, clear_bpy_data


class BaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # FIXME when enabling within test it broke module paths - same classes become are not equal
        # check_addon_enabled(cls.package_name)
        # check_operator_exists()
        pass

    @classmethod
    def tearDownClass(cls):
        # check_addon_disabled(cls.package_name)
        pass

    def setUp(self):
        if bpy.context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')
        deselect_all()
        clear_bpy_data()


def check_addon_enabled(mod):
    result = bpy.ops.preferences.addon_enable(module=mod)
    assert result == {'FINISHED'}, f"Failed to enable addon: {mod}"


def check_addon_disabled(mod):
    result = bpy.ops.preferences.addon_disable(module=mod)
    assert result == {'FINISHED'}, f"Failed to disable addon: {mod}"


def check_operator_exists():
    assert hasattr(bpy.ops, G3djExportOperator.bl_idname), f"Operator not found: {G3djExportOperator.bl_idname}"
    assert hasattr(bpy.ops, G3dbExportOperator.bl_idname), f"Operator not found: {G3dbExportOperator.bl_idname}"

