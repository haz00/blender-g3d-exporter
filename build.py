import hashlib
import sys
import os
from pathlib import Path
import shutil

addon_id = 'g3d_exporter'
source_dir = Path("src")
build_path = Path("build")
appdata_path = Path(os.getenv("APPDATA"))

blender_addon_paths = [
    appdata_path / "Blender Foundation" / "Blender" / "2.83" / "scripts" / "addons",  # lts
    appdata_path / "Blender Foundation" / "Blender" / "2.93" / "scripts" / "addons",  # lts
    appdata_path / "Blender Foundation" / "Blender" / "3.0" / "scripts" / "addons",
    appdata_path / "Blender Foundation" / "Blender" / "3.1" / "scripts" / "addons",
]


def install():
    for addons_path in blender_addon_paths:
        print(f"\ninstall to {addons_path}")

        if (addons_path.exists()):
            shutil.copytree(source_dir, addons_path, dirs_exist_ok=True)


def clean():
    for addons_path in blender_addon_paths:
        addon_home = addons_path / addon_id
        print(f"clean {addon_home}")

        if (addon_home.exists()):
            shutil.rmtree(addon_home)


def zip() -> Path:
    return Path(shutil.make_archive(build_path / addon_id, 'zip', source_dir))


def sign(src: Path):
    with open(src, 'rb') as f:
        buf = f.read()
        md5 = hashlib.md5(buf).hexdigest()
        sha1 = hashlib.sha1(buf).hexdigest()

        dst = src.parent / (src.name + '.hashsum')
        with open(dst, 'w') as f:
            f.write(str(src.name))
            f.write('\nMD5:\t' + md5)
            f.write('\nSHA1:\t' + sha1)


if (__name__ == "__main__"):
    cmd = sys.argv[1]

    if (cmd == "install"):
        install()
    elif (cmd == "zip"):
        sign(zip())
    elif (cmd == "clean"):
        clean()
    else:
        raise ValueError(cmd)
