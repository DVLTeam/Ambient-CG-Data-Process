from .render_utils import *
from tqdm import tqdm

def render_all_materials_canonical(cfg):
    # get the list of materials
    materials = os.listdir(os.path.join(cfg["root_dir"], cfg["dataset_dir"]))
    cache_file = os.path.join(cfg["root_dir"], cfg["render_history_cache_canonical"])

    # get the list of rendered materials
    if os.path.exists(cache_file):
        with open(cache_file, mode='r') as f:
            rendered_files = [s.strip() for s in f.readlines()]
    else:
        rendered_files = []

    for directory in tqdm(materials, desc="Rendering Materials"):
        try:
            if os.path.exists(cache_file):
                if directory in rendered_files:
                    continue
            reset_blender(cfg)
            material, size = get_blender_material(os.path.join(cfg["root_dir"], cfg["dataset_dir"], directory))
            scene = create_scene_with_material(material, size, cfg)
            scene = add_canonical_lighting(scene)
            scene = add_canonical_camera(scene, size)
            render_image(scene, os.path.join(cfg["root_dir"], cfg["dataset_dir"], directory, "canonical_render.png"))
            print("rendered: " + directory)
            with open(cache_file, mode='a') as f:
                f.write(directory + "\n")
        except Exception as e:
            print("failed to render: " + directory)
            print(e)
            continue


def render_specific_material_canonical(cfg, dir_name, output_dir, export_blend=False):
    reset_blender(cfg)
    material, size = get_blender_material(os.path.join(cfg["root_dir"], cfg["dataset_dir"], dir_name))
    scene = create_scene_with_material(material, size, cfg)
    scene = add_canonical_lighting(scene)
    scene = add_canonical_camera(scene, size)
    render_image(scene, os.path.join(output_dir, dir_name + ".png"))
    if export_blend:
        export_scene_as_blend(scene, os.path.join(output_dir, "output.blend"))
