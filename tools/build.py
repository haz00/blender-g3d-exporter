import hashlib
import sys
import os
from pathlib import Path
import shutil
from zipfile import ZipFile

addon_name = "blender_g3d_exporter"

source_home = Path("..")

build_path = Path("build")

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
    appdata_path / "Blender Foundation" / "Blender" / "2.83" / "scripts" / "addons", # lts
    appdata_path / "Blender Foundation" / "Blender" / "2.93" / "scripts" / "addons", # lts
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
    build_path.mkdir(exist_ok=True)

    zip_dst = (build_path / addon_name).with_suffix('.zip')

    with ZipFile(zip_dst, "w") as zf:
        for src in source_files:
            arcname = f"{addon_name}/{src}"
            src = str(source_home / src)
            zf.write(src, arcname)
            print(f"zip {src} to {arcname}")
        print(f"zip done {zf.filename}")
            
    sign(zip_dst)


def clean():
    for addons_path in blender_addon_paths:
        addon_home = addons_path / addon_name
        print(f"clean {addon_home}")

        if (addon_home.exists()):
            shutil.rmtree(addon_home)


def sign(src: Path):
    with open(src, 'rb') as f:
        buf = f.read()
        md5 = hashlib.md5(buf).hexdigest()
        sha1 = hashlib.sha1(buf).hexdigest()

        dst = src.parent / (src.name + '.hashsum')
        print(f"sign {src} to {dst}")

        with open(dst, 'w') as f:
            f.write(str(src.name))
            f.write('\nMD5:\t' + md5)
            f.write('\nSHA1:\t' + sha1)



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
