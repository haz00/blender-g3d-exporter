import logging
import sys
import bpy
from pathlib import Path

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)-20s %(levelname)8s %(name)25s  %(message)s')

demo_dir = Path(__file__).parent
export_file = demo_dir / "assets/demo.g3dj"

sys.path.append(str(demo_dir.parent))

result = bpy.ops.preferences.addon_enable(module='g3d_exporter')
assert result == {'FINISHED'}, "Failed to enable addon"

options = {
    'use_armature': True,
    'use_normal': True,
    'use_actions': True,
    'use_color': True,
    'use_shapekeys': False,
    'fps': 60,
}

bpy.ops.export_scene.g3dj(filepath=str(export_file), **options)
bpy.ops.export_scene.g3db(filepath=str(export_file), **options)
