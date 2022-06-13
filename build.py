"""
cli commands:
    - install
    - uninstall
    - zip
    - test "blender_exe_path"
"""

import hashlib
import subprocess
import sys
import os
from pathlib import Path
import shutil

addon_package = 'g3d_exporter'
source_dir = Path("g3d_exporter")
build_path = Path("build")

appdata_path = Path(os.getenv("APPDATA"))

blender_addon_paths = [
    appdata_path / "Blender Foundation/Blender/2.83/scripts/addons",  # lts
    appdata_path / "Blender Foundation/Blender/2.93/scripts/addons",  # lts
    appdata_path / "Blender Foundation/Blender/3.0/scripts/addons",
    appdata_path / "Blender Foundation/Blender/3.1/scripts/addons",
]


def install():
    for addons_path in blender_addon_paths:

        if addons_path.exists():
            dst = addons_path / addon_package
            dst.mkdir(exist_ok=True)

            print(f"install to {dst}")
            shutil.copytree(source_dir, dst, dirs_exist_ok=True)


def uninstall():
    for addons_path in blender_addon_paths:
        addon_home = addons_path / addon_package
        print(f"uninstall {addon_home}")

        if addon_home.exists():
            shutil.rmtree(addon_home)


def export_zip() -> Path:
    return Path(shutil.make_archive(str(build_path / addon_package), 'zip', source_dir))


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


def run_tests(blend_exe: str):
    script = "tests/runner.py"
    subprocess.run([blend_exe, "--factory-startup", "--background", "-noaudio", "--python", script])


def export_demo(blend_exe: str):
    blend_file = "demo/demo.blend"
    script = "demo/export_script.py"
    print(f"build demo {blend_file}")
    subprocess.run([blend_exe, blend_file, "--factory-startup", "--background", "-noaudio", "--python", script])


if __name__ == "__main__":
    import platform
    if platform.system() != "Windows":
        raise ValueError(f"Host system does not supported by builder: {platform.system()}")

    cmd = sys.argv[1]

    if cmd == "install":
        install()
    elif cmd == "zip":
        sign(export_zip())
    elif cmd == "uninstall":
        uninstall()
    elif cmd == "test":
        run_tests(sys.argv[2])
    elif cmd == "demo":
        export_demo(sys.argv[2])
    else:
        raise ValueError(cmd)
