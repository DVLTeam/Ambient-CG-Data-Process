import os
import bpy
import subprocess
import MaterialX as mx

AMBIENT_NAMINGS = {
    "ao": "AmbientOcclusion",
    "base_color": "Color",
    "displacement": "Displacement",
    "roughness": "Roughness",
    "normal": "NormalGL",
    "emission": "Emission",
    "metallic": "Metalness",
    "opacity": "Opacity",
}


def reset_blender(cfg):
    # Set up the scene
    bpy.ops.wm.read_factory_settings(use_empty=True)  # Create a new empty scene

    if cfg["render_use_gpu"]:
        # Get the Cycles preferences
        cycles_preferences = bpy.context.preferences.addons['cycles'].preferences

        # Enable CUDA
        if cfg["render_use_optix"]:
            cycles_preferences.compute_device_type = 'OPTIX'
        else:
            cycles_preferences.compute_device_type = 'CUDA'

        for device in cycles_preferences.devices:
            if device.type == 'OPTIX' and cfg["render_use_optix"]:
                device.use = True  # Enable this CUDA device
            elif device.type == 'CUDA' and not cfg["render_use_optix"]:
                device.use = True

def get_blender_material(maps_path):
    maps = os.listdir(maps_path)
    # read in all png files, and pare them with names in the AMBIENT_NAMINGS dict
    ambient_maps = {}
    for map in maps:
        if map.endswith(".png") or map.endswith(".PNG"):
            for key in AMBIENT_NAMINGS.keys():
                if map.__contains__(AMBIENT_NAMINGS[key]):
                    ambient_maps[key] = map

    material_name = os.path.basename(maps_path)
    print("creating material: " + material_name)

    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create Shader nodes and connect them
    shader_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader_node.location = (0, 0)
    shader_node.inputs['Specular'].default_value = 0.0

    # ao does not work with principled shader
    # import base color
    if "base_color" in ambient_maps.keys():
        base_color_node = nodes.new(type='ShaderNodeTexImage')
        base_color_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["base_color"])
        base_color_node.location = (-400, 400)
        material.node_tree.links.new(base_color_node.outputs['Color'], shader_node.inputs['Base Color'])

    # import roughness
    if "roughness" in ambient_maps.keys():
        roughness_node = nodes.new(type='ShaderNodeTexImage')
        roughness_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["roughness"])
        roughness_node.location = (-400, 200)
        material.node_tree.links.new(roughness_node.outputs['Color'], shader_node.inputs['Roughness'])

    # import metallic
    if "metallic" in ambient_maps.keys():
        metallic_node = nodes.new(type='ShaderNodeTexImage')
        metallic_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["metallic"])
        metallic_node.location = (-400, 0)
        material.node_tree.links.new(metallic_node.outputs['Color'], shader_node.inputs['Metallic'])

    # import normal
    if "normal" in ambient_maps.keys():
        # add a normal map node
        normal_map_node = nodes.new(type='ShaderNodeNormalMap')
        normal_map_node.location = (-200, 0)
        material.node_tree.links.new(normal_map_node.outputs['Normal'], shader_node.inputs['Normal'])

        normal_node = nodes.new(type='ShaderNodeTexImage')
        normal_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["normal"])
        normal_node.location = (-400, -200)
        material.node_tree.links.new(normal_node.outputs['Color'], normal_map_node.inputs['Color'])

    # import emission
    if "emission" in ambient_maps.keys():
        emission_node = nodes.new(type='ShaderNodeTexImage')
        emission_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["emission"])
        emission_node.location = (-400, -400)
        material.node_tree.links.new(emission_node.outputs['Color'], shader_node.inputs['Emission'])

    # # import opacity
    # if "opacity" in ambient_maps.keys():
    #     opacity_node = nodes.new(type='ShaderNodeTexImage')
    #     opacity_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["opacity"])
    #     opacity_node.location = (-400, -600)
    #     material.node_tree.links.new(opacity_node.outputs['Color'], shader_node.inputs['Alpha'])

    # create a material output node and link it to the shader node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(shader_node.outputs['BSDF'], output_node.inputs['Surface'])

    # import displacement
    if "displacement" in ambient_maps.keys():
        # add a displacement node
        disp_node = nodes.new(type='ShaderNodeDisplacement')
        disp_node.location = (-200, 0)
        material.node_tree.links.new(disp_node.outputs['Displacement'], output_node.inputs['Displacement'])

        displacement_node = nodes.new(type='ShaderNodeTexImage')
        displacement_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["displacement"])
        displacement_node.location = (-400, -400)
        material.node_tree.links.new(displacement_node.outputs['Color'], disp_node.inputs['Height'])

        disp_node.inputs['Scale'].default_value = 0.002

    # Set displacement method
    material.cycles.displacement_method = 'BOTH'

    # Return the created material
    return material


# this function generates a canonical 2d surface and a light source from above as a blender scene
def create_scene_with_material(material, cfg):

    # set the scene render engine to cycles
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if cfg["render_use_gpu"]:
        scene.cycles.device = 'GPU'
        if cfg["render_use_optix"] and cfg["render_use_denoiser"]:
            scene.cycles.denoiser = 'OPTIX'

    # delete all objects in the scene
    for obj in scene.objects:
        bpy.data.objects.remove(obj)

    # Create a mesh object with a single 1m x 1m square face
    mesh = bpy.data.meshes.new(name='SquareMesh')
    vertices = [(-0.5, -0.5, 0), (-0.5, 0.5, 0), (0.5, 0.5, 0), (0.5, -0.5, 0)]
    edges = []
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()

    # Create an object from the mesh and link it to the scene
    obj = bpy.data.objects.new('SquareObject', mesh)
    scene.collection.objects.link(obj)

    # Assign the material to the object
    obj.data.materials.append(material)

    # subsurf_mod = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    #
    # # Set the subdivision levels
    # subsurf_mod.levels = 11
    # subsurf_mod.render_levels = 11  # Optional: if you want the subdivision to apply in renders as well
    # subsurf_mod.subdivision_type = 'SIMPLE'

    # Set up UV mapping so the material is applied exactly once without repetition
    uv_map = obj.data.uv_layers.new(name="UVMap")
    uv_map.data[0].uv = (0, 0)
    uv_map.data[1].uv = (1, 0)
    uv_map.data[2].uv = (1, 1)
    uv_map.data[3].uv = (0, 1)

    return scene


# adds a point light source to the scene on the top of the middle of the tile
def add_canonical_lighting(scene, position=(0, 0, 0.5), intensity=10, color=(1, 1, 1)):
    # Ensure the scene parameter is valid
    if not scene:
        raise ValueError("Invalid scene")

    # Create a point light source and link it to the scene
    light_data = bpy.data.lights.new(name="Light", type='POINT')
    light_data.energy = intensity
    light_data.color = color
    light_object = bpy.data.objects.new(name="Light", object_data=light_data)
    scene.collection.objects.link(light_object)

    # Position the light source
    light_object.location = position

    return scene


def add_canonical_camera(scene, position=(0, 0, 10), plane_size=1000, focal_length=10000):
    # Ensure the scene parameter is valid
    if not scene:
        raise ValueError("Invalid scene")

    # Create a camera and link it to the scene
    camera_data = bpy.data.cameras.new(name="Camera")
    camera_object = bpy.data.objects.new(name="Camera", object_data=camera_data)
    scene.collection.objects.link(camera_object)

    # Position the camera
    camera_object.location = position

    # Set the focal length
    camera_object.data.lens = focal_length

    # set the sensor size
    camera_object.data.sensor_width = plane_size
    camera_object.data.sensor_height = plane_size

    # set resolution
    scene.render.resolution_x = 4096
    scene.render.resolution_y = 4096

    scene.camera = camera_object

    return scene


def export_scene_as_blend(scene, file_path):
    # Ensure the scene parameter is valid
    if not scene:
        raise ValueError("Invalid scene")

    # Set the active scene to the provided scene
    bpy.context.window.scene = scene

    # Save the current blend file to the specified file path
    bpy.ops.wm.save_as_mainfile(filepath=file_path)


def render_image(scene, output_path):
    # Ensure the scene parameter is valid
    if not scene:
        raise ValueError("Invalid scene")

    # Set the active scene to the provided scene
    bpy.context.window.scene = scene

    # Set the output path
    scene.render.filepath = output_path

    # Render the scene
    bpy.ops.render.render(write_still=True)
