@echo off

for %%I in (.) do SET cur_dir_name=%%~nxI

SET inputs=%cur_dir_name%\generator.py 
SET inputs=%inputs% %cur_dir_name%\domain.py 
SET inputs=%inputs% %cur_dir_name%\export_operator.py 
SET inputs=%inputs% %cur_dir_name%\__init__.py 
SET inputs=%inputs% %cur_dir_name%\utils.py 
SET inputs=%inputs% %cur_dir_name%\g3dj_encoder.py 
SET inputs=%inputs% %cur_dir_name%\LICENSE 

SET out_path=%cur_dir_name%\blender_g3d_exporter.zip

CD ..
IF EXIST %out_path% DEL /F %out_path%
7z a -tZip -sse -stl -scrcsha1 %out_path% %inputs% 
7z h -scrcsha1 %out_path%
CD %cur_dir_name%

@pause