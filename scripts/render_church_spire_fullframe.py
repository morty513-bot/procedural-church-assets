import bpy
import math
import os
from mathutils import Vector

BASE = "/home/azureuser/.openclaw/workspace/assets/church_spire"
blend = os.path.join(BASE, "church_spire_lowpoly.blend")

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

cam = scene.camera
if cam is None:
    raise RuntimeError('No camera found')

root = bpy.data.objects.get('ChurchSpire')
if root is None:
    raise RuntimeError('ChurchSpire root not found')

# Collect world-space bbox corners for all mesh children under root
pts = []
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    if obj.name == 'Ground':
        continue
    if obj.parent != root and obj != root:
        continue
    for c in obj.bound_box:
        pts.append(obj.matrix_world @ Vector(c))

if not pts:
    raise RuntimeError('No mesh points found for spire')

min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (min_v + max_v) * 0.5
height = max_v.z - min_v.z

# Ensure full-height framing by targeting vertical center and backing up enough.
# For 16:9 horizontal frame, vertical FOV is limiting dimension.
fov = cam.data.angle_y if cam.data.sensor_fit != 'VERTICAL' else cam.data.angle
half_h = (height * 0.5) * 1.15  # margin
radius = half_h / math.tan(fov * 0.5)
# Extra room for width/depth and perspective
radius *= 1.35

angles = [35, 90, 145]
for i, a in enumerate(angles, start=1):
    rad = math.radians(a)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    cam.location.z = center.z

    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    out = os.path.join(BASE, f'preview_fullframe_{i}.png')
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)

print('DONE')
