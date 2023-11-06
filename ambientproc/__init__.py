import subprocess
import sys
import pkg_resources

required = {"numpy", "torch", "lmdb", "blender", "MaterialX"}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed



from .downloads import *
from .utilities import *
from .render_utils import *
from .render_textures_canonical import *
from .pytroch_datasets import *

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
    'render_image',
    'reset_blender',

    'render_all_materials_canonical',
    'render_specific_material_canonical',

    'AmbientDataset',
    'AmbientDataConfig'
]