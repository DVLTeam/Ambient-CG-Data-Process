import os
import bpy
import subprocess
import MaterialX as mx

AMBIENT_NAMINGS = {
    "ao" : "AmbientOcclusion",
    "base_color" : "Color",
    "displacement" : "Displacement",
    "roughness" : "Roughness",
    "normal" : "NormalGL",
    "emission" : "Emission",
    "metallic" : "Metalness",
    "opacity" : "Opacity",
}

def reset_blender():
    # Set up the scene
    bpy.ops.wm.read_factory_settings(use_empty=True)  # Create a new empty scene

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

    # ao does not work with principled shader
    # import base color
    if "base_color" in ambient_maps.keys():
        base_color_node = nodes.new(type='ShaderNodeTexImage')
        base_color_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["base_color"])
        base_color_node.location = (-400, 400)
        material.node_tree.links.new(base_color_node.outputs['Color'], shader_node.inputs['Base Color'])

    # import roughness
    if "roughness" in ambient_maps.keys():
        roughness_node = nodes.new(type='ShaderNodeTexImadisplacement_nodege')
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

    # import opacity
    if "opacity" in ambient_maps.keys():
        opacity_node = nodes.new(type='ShaderNodeTexImage')
        opacity_node.image = bpy.data.images.load(maps_path + "/" + ambient_maps["opacity"])
        opacity_node.location = (-400, -600)
        material.node_tree.links.new(opacity_node.outputs['Color'], shader_node.inputs['Alpha'])

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

    # Return the created material
    return material

# this function generates a canonical 2d surface and a light source from above as a blender scene
def create_scene_with_material(material):
    # Ensure the material parameter is valid
    if not material:
        raise ValueError("Invalid material")

    scene = bpy.context.scene

    # set the scene render engine to cycles
    scene.render.engine = 'CYCLES'

    # delete all objects in the scene
    for obj in scene.objects:
        bpy.data.objects.remove(obj)

    # Create a mesh object with a single 1m x 1m square face
    mesh = bpy.data.meshes.new(name='SquareMesh')
    vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    edges = []
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()

    # Create an object from the mesh and link it to the scene
    obj = bpy.data.objects.new('SquareObject', mesh)
    scene.collection.objects.link(obj)

    # Assign the material to the object
    obj.data.materials.append(material)

    # Set up UV mapping so the material is applied exactly once without repetition
    uv_map = obj.data.uv_layers.new(name="UVMap")
    uv_map.data[0].uv = (0, 0)
    uv_map.data[1].uv = (1, 0)
    uv_map.data[2].uv = (1, 1)
    uv_map.data[3].uv = (0, 1)

    return scene


def export_scene_as_blend(scene, file_path):
    # Ensure the scene parameter is valid
    if not scene:
        raise ValueError("Invalid scene")

    # Set the active scene to the provided scene
    bpy.context.window.scene = scene

    # Save the current blend file to the specified file path
    bpy.ops.wm.save_as_mainfile(filepath=file_path)


