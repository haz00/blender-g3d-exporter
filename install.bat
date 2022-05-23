@echo off

set blender_addons="%appdata%\Blender Foundation\Blender\3.0\scripts\addons"
set addon_home=%blender_addons%\blender_g3d_exporter

if not exist %addon_home% mrdir %addon_home%

copy /Y generator.py %addon_home%
copy /Y domain.py %addon_home%
copy /Y export_operator.py %addon_home%
copy /Y __init__.py %addon_home%
copy /Y utils.py %addon_home%
copy /Y g3dj_encoder.py %addon_home%
copy /Y LICENSE %addon_home%

@pause