"""
cli commands:
    - install
    - uninstall
    - zip
    - test blender_exe_path [test_case] [test_case]...
        test_case - Fully qualified path to test. Examples:
                    tests.builder_test.G3dBuilderTest
                    tests.builder_test.G3dBuilderTest.test_flags
"""

import hashlib
import subprocess
import sys
import os
import platform
from pathlib import Path
import shutil
from typing import List

addon_package = 'g3d_exporter'
source_dir = Path("g3d_exporter")
build_path = Path("build")

def addon_install_path():
    osname = platform.system()
    if osname == "Linux":
        return os.path.join(os.getenv("HOME"), ".config/blender")
    elif osname == "Windows":
        return os.path.join(os.getenv("APPDATA"), "Blender Foundation/Blender")
    else:
        os.exit(0)

blender_addon_versions = [
    "2.8",  # lts
    "2.9",  # lts
    "3.0",
    "3.1",
    "3.2",
    "3.3",  # lts
    "3.4",
    "3.5",
    "3.6",  # lts
]

def install():
    for addon_version in blender_addon_versions:
        addon_path = Path(os.path.join(addon_install_path(), addon_version))
        if addon_path.exists():

            # check scripts/addons exist
            scipts_folder = addon_path / Path("scripts")
            addons_folder = scipts_folder / Path("addons")
            if scipts_folder.exists() == False:
                scipts_folder.mkdir()
                addons_folder.mkdir()

            dst = addons_folder / addon_package
            dst.mkdir(exist_ok=True)

            print(f"install to {dst}")
            shutil.copytree(source_dir, dst, dirs_exist_ok=True)


def uninstall():
    for addon_version in blender_addon_versions:
        addon_path = Path(os.path.join(addon_install_path(), addon_version))
        if addon_path.exists():

            scipts_folder = addon_path / Path("scripts")
            addons_folder = scipts_folder / Path("addons")
            dst = addons_folder / addon_package
            if dst.exists() == False:
                continue

            print(f"uninstall: {dst}")
            shutil.rmtree(dst)


def export_zip() -> Path:
    src_dst = build_path / "tmp" / addon_package
    src_dst.mkdir(exist_ok=True, parents=True)

    print(f"copy to {src_dst}")
    shutil.copytree(source_dir, src_dst, dirs_exist_ok=True)

    print(f"clean to {src_dst}")
    dst = Path(shutil.make_archive(str(build_path / addon_package), 'zip', src_dst.parent))
    shutil.rmtree(src_dst.parent)

    return dst


def sign(src: Path):
    with open(src, 'rb') as f:
        buf = f.read()
        md5 = hashlib.md5(buf).hexdigest()
        sha1 = hashlib.sha1(buf).hexdigest()

        dst = src.parent / (src.name + '.hashsum')
        with open(dst, 'w') as ff:
            ff.write(str(src.name))
            ff.write('\nMD5:\t' + md5)
            ff.write('\nSHA1:\t' + sha1)


def run_tests(blend_exe: str, args: List[str]):
    script = "tests/runner.py"
    subprocess.run([blend_exe, "--factory-startup", "--background", "-noaudio", "--python", script, "--", *args])


def export_demo(blend_exe: str):
    blend_file = "demo/demo.blend"
    script = "demo/export_script.py"
    print(f"build demo {blend_file}")
    subprocess.run([blend_exe, blend_file, "--factory-startup", "--background", "-noaudio", "--python", script])


if __name__ == "__main__":
    import platform
    if (platform.system() == "Windows" or platform.system() == "Linux") == False:
        raise ValueError(f"Host system does not supported by builder: {platform.system()}")

    cmd = sys.argv[1]

    print(f"command: {cmd}")

    if cmd == "install":
        install()
    elif cmd == "zip":
        sign(export_zip())
    elif cmd == "uninstall":
        uninstall()
    elif cmd == "test":
        run_tests(sys.argv[2], sys.argv[3:])
    elif cmd == "demo":
        export_demo(sys.argv[2])
    else:
        raise ValueError(cmd)
