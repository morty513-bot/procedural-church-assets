import bpy, os, math
from mathutils import Vector

SRC = '/home/azureuser/.openclaw/workspace/procedural-church-assets/assets/french_house_v3/french_house_v3.blend'
OUT_DIR = '/home/azureuser/.openclaw/workspace/procedural-church-assets/assets/french_house_v3'

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.eevee.taa_render_samples = 16

pts = []
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    if obj.name.lower() in {'ground', 'plane'}:
        continue
    for c in obj.bound_box:
        pts.append(obj.matrix_world @ Vector(c))

if not pts:
    raise RuntimeError('No mesh bounds found')

min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (min_v + max_v) * 0.5
height = max_v.z - min_v.z

cam = scene.camera
if cam is None:
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    scene.camera = cam

fov = cam.data.angle_y
half_h = (height * 0.5) * 1.40
radius = (half_h / max(math.tan(fov * 0.5), 1e-4)) * 1.35
look = center.copy()
look.z = center.z + 0.05

angles = [35, 90, 145]
for i, a in enumerate(angles, start=1):
    rad = math.radians(a)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    cam.location.z = center.z + 0.45
    d = look - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT_DIR, f'preview_checked_{i}.png')
    bpy.ops.render.render(write_still=True)

cam.location = Vector((center.x + radius * 0.62, center.y - radius * 0.68, center.z + height * 0.22))
d = (center + Vector((0, 0, height * 0.2))) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = os.path.join(OUT_DIR, 'preview_checked_detail.png')
bpy.ops.render.render(write_still=True)

print('DONE', OUT_DIR)
