# <pep8 compliant>

import bpy
import sys
from pathlib import Path
import importlib

module_path = str(Path(bpy.data.filepath).parents[1])

if module_path not in sys.path:
    # add parent directory to classpath
    sys.path.append(module_path)
        
import utils
import domain
import g3dj_encoder
import generator
import export_operator
    
# reload scripts
importlib.reload(utils)
importlib.reload(domain)
importlib.reload(g3dj_encoder)
importlib.reload(generator)
importlib.reload(export_operator)

# relative to .blend
assets_basedir = Path(bpy.data.filepath).parent / "assets"

def export_demo(name: str, gen: generator.G3dGenerator, objects: list[bpy.types.Object] = None):
    print('export_demo', name) 
    
    root_collection = bpy.data.scenes['Scene'].collection
    if (objects == None):
        objects = root_collection.children[name].objects 
    
    file = assets_basedir / f"{name}.g3dj"
    export_operator.do_export(file, gen, objects)

default_gen = generator.G3dGenerator()

no_shapes_gen = generator.G3dGenerator()
no_shapes_gen.use_shapekeys = False

export_demo('simple', no_shapes_gen)
export_demo('shapekeys', default_gen)
export_demo('skeleton', no_shapes_gen)
export_demo('animation', no_shapes_gen)
export_demo('animation and shapekeys', default_gen)
export_demo('complex', default_gen)
#export_demo('selected', default_gen, bpy.context.selected_objects)