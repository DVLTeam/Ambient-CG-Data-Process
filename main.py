from ambientproc import *

cfg = load_config()
reset_blender(cfg)
material = get_blender_material(cfg["root_dir"] + "/dataset/Gravel033")
scene = create_scene_with_material(material, cfg)
scene = add_canonical_lighting(scene)
scene = add_canonical_camera(scene)
# export_scene_as_blend(scene, "out.blend")
render_image(scene, "Gravel033.png")