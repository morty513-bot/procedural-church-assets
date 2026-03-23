import bpy
import os
import math
from mathutils import Vector

SRC_BLEND = "/home/mainuser/.openclaw/workspace/assets/church_spire_v2/church_spire_v2.blend"
OUT = "/home/mainuser/.openclaw/workspace/assets/church_spire_v4"
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 576
scene.eevee.taa_render_samples = 16

# --- Strongly contrasted materials ---
stone = bpy.data.materials.new("StoneV4")
stone.use_nodes = True
s = stone.node_tree.nodes['Principled BSDF']
s.inputs['Base Color'].default_value = (0.83, 0.79, 0.70, 1)  # warm sandstone
s.inputs['Roughness'].default_value = 0.92

roof = bpy.data.materials.new("RoofV4")
roof.use_nodes = True
r = roof.node_tree.nodes['Principled BSDF']
r.inputs['Base Color'].default_value = (0.06, 0.08, 0.16, 1)  # dark blue slate
r.inputs['Roughness'].default_value = 0.6

window = bpy.data.materials.new("WindowV4")
window.use_nodes = True
w = window.node_tree.nodes['Principled BSDF']
w.inputs['Base Color'].default_value = (0.15, 0.65, 0.95, 1)  # bright cyan glass
w.inputs['Transmission Weight'].default_value = 0.8
w.inputs['Roughness'].default_value = 0.02

metal = bpy.data.materials.new("MetalV4")
metal.use_nodes = True
m = metal.node_tree.nodes['Principled BSDF']
m.inputs['Base Color'].default_value = (0.95, 0.79, 0.22, 1)  # bright gold
m.inputs['Metallic'].default_value = 0.95
m.inputs['Roughness'].default_value = 0.2

# Identify objects
objs = list(scene.objects)
window_objs = []
for o in objs:
    if o.type != 'MESH':
        continue
    # In v2 script windows are thin cubes with tiny Y scale and medium Z scale
    if o.name.startswith('Cube') and o.scale.y < 0.03 and o.scale.z > 0.25:
        window_objs.append(o)

# Make windows bigger (height+width), slightly thicker for readability
for wo in window_objs:
    wo.scale.x *= 1.8
    wo.scale.z *= 1.9
    wo.scale.y = max(wo.scale.y * 1.6, 0.035)

# Assign materials with high contrast
for o in objs:
    if o.type != 'MESH':
        continue
    o.data.materials.clear()
    lname = o.name.lower()

    if o in window_objs:
        o.data.materials.append(window)
    elif 'cone' in lname:
        o.data.materials.append(roof)
    elif 'sphere' in lname or (lname.startswith('cube') and o.location.z > 12 and o.scale.z > 2.0):
        o.data.materials.append(metal)
    elif lname == 'plane':
        g = bpy.data.materials.new('GroundV4')
        g.use_nodes = True
        gb = g.node_tree.nodes['Principled BSDF']
        gb.inputs['Base Color'].default_value = (0.90, 0.92, 0.94, 1)
        gb.inputs['Roughness'].default_value = 0.95
        o.data.materials.append(g)
    else:
        o.data.materials.append(stone)

# Render same three angles
cam = scene.camera
target = bpy.data.objects.get('ChurchSpireV2')
cx, cy, cz = (0.0, 0.0, 6.5)
if target:
    cx, cy = target.location.x, target.location.y

radius = ((cam.location.x - cx) ** 2 + (cam.location.y - cy) ** 2) ** 0.5
if radius < 1:
    radius = 14.0

for i, ang in enumerate([35, 90, 145], start=1):
    rad = math.radians(ang)
    cam.location.x = cx + radius * math.cos(rad)
    cam.location.y = cy + radius * math.sin(rad)
    cam.location.z = cz
    direction = Vector((cx, cy, cz)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    scene.render.filepath = os.path.join(OUT, f'preview_v4_{i}.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v4.blend'))
print('DONE', OUT)
