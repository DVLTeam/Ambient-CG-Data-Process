import subprocess
import sys
import pkg_resources

required = {"numpy", "torch", "lmdb", "blender", "MaterialX"}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    print(f"Installing missing packages for ambientcgproc: {missing}")
    python = sys.executable
    subprocess.check_call([python, "-m", "pip", "install", *missing], stdout=subprocess.DEVNULL)

from .downloads import get_download_csv, download_materials, unzip_datasets, download
from .utilities import load_config
from .render_utils import get_blender_material, \
    create_scene_with_material, export_scene_as_blend, \
    add_canonical_lighting, add_canonical_camera, \
    render_image

__all__ = [
    'load_config',
    'get_download_csv',
    'download_materials',
    'unzip_datasets',
    'download',

    'get_blender_material',
    'create_scene_with_material',
    'export_scene_as_blend',
    'add_canonical_lighting',
    "add_canonical_camera",
    'render_image'
]