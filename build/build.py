from fileinput import filename
import hashlib
import sys
import os
from pathlib import Path
import shutil
from zipfile import ZipFile

addon_name = "blender_g3d_exporter"

source_home = Path("..")

artifacts_home = Path("out")

source_files = [
    "generator.py",
    "domain.py",
    "export_operator.py",
    "__init__.py",
    "utils.py",
    "g3dj_encoder.py",
    "LICENSE",
]

appdata_path = Path(os.getenv("APPDATA"))

blender_addon_paths = [
    appdata_path / "Blender Foundation" / "Blender" / "2.83" / "scripts" / "addons",
    appdata_path / "Blender Foundation" / "Blender" / "2.93" / "scripts" / "addons",
    appdata_path / "Blender Foundation" / "Blender" / "3.0" / "scripts" / "addons",
    appdata_path / "Blender Foundation" / "Blender" / "3.1" / "scripts" / "addons",
]


def install():
    for addons_path in blender_addon_paths:
        print(f"\ninstall to {addons_path}")

        if (addons_path.exists()):
            dst = addons_path / addon_name
            dst.mkdir(parents=True, exist_ok=True)

            for src in source_files:
                src = source_home / src
                print(f"copy {src} to {dst}")
                shutil.copy(src, dst)


def zip():
    artifacts_home.mkdir(exist_ok=True)

    zip_dst = (artifacts_home / addon_name).with_suffix('.zip')

    with ZipFile(zip_dst, "w") as zf:

        for src in source_files:
            arcname = f"{addon_name}/{src}"
            src = str(source_home / src)
            zf.write(src, arcname)
            print(f"zip {src} to {arcname}")
            
        print(f"zip done {zf.filename}")

        sign(zip_dst, zip_dst.parent / (zip_dst.name + '.sum'))


def clean():
    for addons_path in blender_addon_paths:
        addon_home = addons_path / addon_name
        print(f"clean {addon_home}")

        if (addon_home.exists()):
            for src in source_files:
                dst = addon_home / src
                os.remove(dst)
                print(f"remove {dst}")
            addon_home.rmdir()


def sign(src, dst):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    with open(src, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            md5.update(data)
            sha1.update(data)

    with open(dst, 'w') as f:
        f.write(str(src))
        f.write('\nMD5: ' + md5.hexdigest())
        f.write('\nSHA1: ' + sha1.hexdigest())


def main():
    cmd = sys.argv[1]

    if (cmd == "install"):
        install()
    elif (cmd == "zip"):
        zip()
    elif (cmd == "clean"):
        clean()
    else:
        raise ValueError(cmd)


if (__name__ == "__main__"):
    main()
