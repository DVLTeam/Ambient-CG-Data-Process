from ambientproc import *

cfg = load_config()
material = get_blender_material(cfg["root_dir"] + "/dataset/Gravel033")
scene = create_scene_with_material(material)
export_scene_as_blend(scene, "./out.blend")