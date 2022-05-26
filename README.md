# !!!WORK IN PROGRESS!!!

# Overview
Export Blender scene to native LibGDX model format.

The demo folder contains LibGDX project with examples.

## Features
- Blender 2.83 LTS, 2.93 LTS, 3.0, 3.1
- Y-up
- Bake bone animations
- Vertex attributes customization
- Export shapekeys as separate file (see [shapekeys loader](https://github.com/haz00/g3d-model-shape))

Note that LibGDX default shader does not handle normal mapping and other rich PRB features out of the box. The addon can export such attributes though. You should provide your own shader if you need it.

# Usage
### Installation
1. Download latest version from [release page](https://github.com/haz00/blender-g3d-exporter/releases)
2. Blender - Settings - Addons - Import
3. Do not forget enable checkbox
4. File - Export - .g3dj
5. Follow addon settings

# Useful links
[LibGDX Model user guide](https://libgdx.com/wiki/graphics/3d/quick-start)

[G3D Specification](https://github.com/libgdx/fbx-conv/wiki/Version-0.1-%28libgdx-0.9.9%29)

https://docs.blender.org/api/current/info_quickstart.html

https://docs.blender.org/api/current/info_tips_and_tricks.html#executing-modules

https://docs.blender.org/manual/en/latest/advanced/scripting/index.html

# TODO
- Multiple uv maps
- Optimize animation keyframes
- g3db

# License
GNU GPLv3 [LICENSE](https://github.com/haz00/blender-g3d-exporter/blob/master/LICENSE)

blender-g3d-exporter Copyright (C) 2022 haz00 (haz00ku@gmail.com)

# Credits
Json formatter based on part of [other addon](https://github.com/Dancovich/libgdx_blender_g3d_exporter)
