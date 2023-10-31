from ambientproc import *

cfg = load_config()
material = get_blender_material(cfg["root_dir"] + "/dataset/PaintedMetal002")
scene = create_scene_with_material(material)
scene = add_canonical_lighting(scene)
scene = add_canonical_camera(scene)
render_image(scene, "PaintedMetal002.png")