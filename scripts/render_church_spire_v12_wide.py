import bpy, os, math
from mathutils import Vector

SRC='/home/mainuser/.openclaw/workspace/assets/church_spire_v12/church_spire_v12.blend'
OUT='/home/mainuser/.openclaw/workspace/assets/church_spire_v12_wide'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.eevee.taa_render_samples=16

cam=scene.camera
target = bpy.data.objects.get('ChurchSpireV2') or bpy.data.objects.get('ChurchSpire')
center = Vector((0,0,6.5))
if target:
    center = target.location.copy()
    center.z = 6.5

# Compute current radius and widen significantly
radius = ((cam.location.x-center.x)**2 + (cam.location.y-center.y)**2) ** 0.5
if radius < 1:
    radius = 11
radius *= 1.55  # zoom out

# Slightly raise camera target so base stays visible with headroom
look = center.copy()
look.z = 6.2

for i, ang in enumerate([35, 90, 145], start=1):
    rad = math.radians(ang)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    cam.location.z = center.z + 0.6
    d = look - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'preview_v12_wide_{i}.png')
    bpy.ops.render.render(write_still=True)

print('DONE', OUT)
