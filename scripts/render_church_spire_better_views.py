import bpy
import math
import os

BASE = "/home/mainuser/.openclaw/workspace/assets/church_spire"
blend = os.path.join(BASE, "church_spire_lowpoly.blend")

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

cam = scene.camera
if cam is None:
    raise RuntimeError('No camera found')

# Aim a little higher so the full spire is visible
target = bpy.data.objects.get('ChurchSpire')
if target is None:
    target_loc = bpy.context.scene.cursor.location.copy()
else:
    target_loc = target.location.copy()

target_loc.z = 6.3

angles = [35, 90, 145]
for i, a in enumerate(angles, start=1):
    r = 14.0
    z = 8.5
    rad = math.radians(a)
    cam.location.x = r * math.cos(rad)
    cam.location.y = r * math.sin(rad)
    cam.location.z = z

    direction = target_loc - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    out = os.path.join(BASE, f'preview_better_{i}.png')
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)

print('DONE')
