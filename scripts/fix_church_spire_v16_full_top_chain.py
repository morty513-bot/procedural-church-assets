import bpy, os, math
from mathutils import Vector

SRC='/home/mainuser/.openclaw/workspace/assets/church_spire_v15/church_spire_v15.blend'
OUT='/home/mainuser/.openclaw/workspace/assets/church_spire_v16'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.eevee.taa_render_samples=16

def z_bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    zs = [p.z for p in pts]
    return min(zs), max(zs)

def xy_dist_from_center(obj):
    loc = obj.matrix_world.translation
    return (loc.x**2 + loc.y**2) ** 0.5

# Determine central-axis objects only (exclude side ornaments)
core = []
for o in scene.objects:
    if o.type != 'MESH' or o.name.lower() == 'plane':
        continue
    d = xy_dist_from_center(o)
    mn, mx = z_bounds(o)
    h = mx - mn
    if d <= 0.55:
        core.append((o, mn, mx, h, d))

core.sort(key=lambda t: t[1])

eps = 0.015

# Start locking from the upper transition/top stack (roughly above 6.8m)
start_idx = 0
for i, (_, mn, _, _, _) in enumerate(core):
    if mn >= 6.8:
        start_idx = i
        break

# Enforce contiguous contact through entire upper chain
for i in range(start_idx, len(core) - 1):
    lower, _, lmax, _, _ = core[i]
    upper, umin, _, _, _ = core[i + 1]
    desired_umin = lmax - eps
    dz = desired_umin - umin
    if abs(dz) > 1e-7:
        upper.location.z += dz
        # refresh cached bounds from this upper onward
        for j in range(i + 1, len(core)):
            o, _, _, _, d = core[j]
            mn, mx = z_bounds(o)
            core[j] = (o, mn, mx, mx - mn, d)

# Wide framing from global mesh bounds
pts = []
for o in scene.objects:
    if o.type != 'MESH' or o.name.lower() == 'plane':
        continue
    for c in o.bound_box:
        pts.append(o.matrix_world @ Vector(c))

min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (min_v + max_v) * 0.5
height = max_v.z - min_v.z

cam = scene.camera
fov = cam.data.angle_y
half_h = (height * 0.5) * 1.35
radius = (half_h / max(math.tan(fov * 0.5), 1e-4)) * 1.32
look = center.copy()
look.z = center.z + 0.1

for i, a in enumerate([35, 90, 145], start=1):
    rad = math.radians(a)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    cam.location.z = center.z + 0.7
    d = look - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'preview_v16_wide_{i}.png')
    bpy.ops.render.render(write_still=True)

# Detail shot focused on top chain
cam.location = Vector((center.x + radius * 0.55, center.y - radius * 0.55, center.z + height * 0.28))
d = (center + Vector((0, 0, height * 0.28))) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = os.path.join(OUT, 'preview_v16_detail.png')
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v16.blend'))

bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type == 'MESH' and o.name.lower() != 'plane':
        o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'church_spire_v16.glb'), export_format='GLB', use_selection=True)

with open(os.path.join(OUT, 'FIX_NOTES_v16.md'), 'w') as f:
    f.write('# v16 full top-chain lock\n')
    f.write(f'- Overlap epsilon: {eps} m\n')
    f.write(f'- Chain lock start index: {start_idx} (minZ >= 6.8)\n\n')
    f.write('## Core objects after fix (ordered by minZ)\n')
    for o, mn, mx, h, dxy in core:
        f.write(f'- {o.name}: minZ={mn:.4f}, maxZ={mx:.4f}, h={h:.4f}, dXY={dxy:.4f}\n')

print('DONE', OUT)
