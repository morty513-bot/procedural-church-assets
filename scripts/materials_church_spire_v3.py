import bpy
import os

BASE = "/home/mainuser/.openclaw/workspace/assets/church_spire_v2"
blend = os.path.join(BASE, "church_spire_v2.blend")
OUT = "/home/mainuser/.openclaw/workspace/assets/church_spire_v3"
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 576
scene.eevee.taa_render_samples = 16

# Helper to build procedural material quickly
def make_stone_mat(name="StoneV3"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")

    noise.inputs[2].default_value = 5.0
    noise.inputs[3].default_value = 6.0
    noise.inputs[4].default_value = 0.55

    ramp.color_ramp.elements[0].color = (0.52, 0.54, 0.58, 1)
    ramp.color_ramp.elements[1].color = (0.70, 0.72, 0.76, 1)

    bsdf.inputs['Roughness'].default_value = 0.88
    bsdf.inputs['Specular IOR Level'].default_value = 0.2

    bump.inputs['Strength'].default_value = 0.18

    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    return mat

def make_roof_mat(name="RoofV3"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    wave = nodes.new("ShaderNodeTexWave")
    noise = nodes.new("ShaderNodeTexNoise")
    mix = nodes.new("ShaderNodeMixRGB")
    bump = nodes.new("ShaderNodeBump")

    wave.wave_type = 'BANDS'
    wave.inputs['Scale'].default_value = 24.0
    wave.inputs['Distortion'].default_value = 2.2

    noise.inputs['Scale'].default_value = 10.0

    mix.blend_type = 'MULTIPLY'
    mix.inputs['Color1'].default_value = (0.20, 0.22, 0.26, 1)
    mix.inputs['Fac'].default_value = 0.55

    bsdf.inputs['Roughness'].default_value = 0.72

    bump.inputs['Strength'].default_value = 0.08

    links.new(wave.outputs['Color'], mix.inputs['Color2'])
    links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    return mat

def make_window_mat(name="WindowV3"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.18, 0.30, 0.42, 1)
    bsdf.inputs['Transmission Weight'].default_value = 0.85
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['IOR'].default_value = 1.45
    return mat

def make_metal_mat(name="MetalV3"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.75, 0.67, 0.45, 1)
    bsdf.inputs['Metallic'].default_value = 0.85
    bsdf.inputs['Roughness'].default_value = 0.25
    return mat

stone = make_stone_mat()
roof = make_roof_mat()
window = make_window_mat()
metal = make_metal_mat()

for obj in scene.objects:
    if obj.type != 'MESH':
        continue

    n = obj.name.lower()
    if obj.data.materials:
        obj.data.materials.clear()

    if 'cone' in n:
        obj.data.materials.append(roof)
    elif 'sphere' in n or (n.startswith('cube') and obj.scale.z > 2.0 and obj.location.z > 12):
        obj.data.materials.append(metal)
    elif 'cube' in n and obj.scale.y < 0.03 and obj.scale.z > 0.3:
        obj.data.materials.append(window)
    elif n == 'plane':
        g = bpy.data.materials.new(name='GroundV3')
        g.use_nodes = True
        b = g.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (0.86, 0.87, 0.88, 1)
        b.inputs['Roughness'].default_value = 0.95
        obj.data.materials.append(g)
    else:
        obj.data.materials.append(stone)

# Render with same camera at 3 stored preview angles by rotating camera around target
cam = scene.camera
target = bpy.data.objects.get('ChurchSpireV2')
center = target.location.copy() if target else bpy.context.scene.cursor.location.copy()
center.z = 6.5

import math
angles = [35, 90, 145]
radius = ((cam.location.x-center.x)**2 + (cam.location.y-center.y)**2) ** 0.5
if radius < 1:
    radius = 14

for i, a in enumerate(angles, start=1):
    rad = math.radians(a)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'preview_v3_{i}.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v3.blend'))
print('DONE', OUT)
