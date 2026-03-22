import bpy, os, math
from mathutils import Vector

SRC = '/home/azureuser/.openclaw/workspace/assets/church_spire_v12/church_spire_v12.blend'
OUT_DIR = '/home/azureuser/.openclaw/workspace/assets/church_spire_v13'
BLEND_OUT = os.path.join(OUT_DIR, 'church_spire_v13.blend')
GLB_OUT = os.path.join(OUT_DIR, 'church_spire_v13.glb')
EPS = 0.02

os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene

STACK = ['Cone.001', 'Cylinder.001', 'Sphere', 'Cube.005', 'Cube.006']

def get_obj(name):
    o = bpy.data.objects.get(name)
    if o is None:
        raise RuntimeError(f'Missing object: {name}')
    return o

def z_bounds(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = obj.evaluated_get(dg)
    if oe.type != 'MESH':
        raise RuntimeError(f'Object {obj.name} is not mesh ({oe.type})')
    mesh = oe.to_mesh()
    try:
        zs = [(oe.matrix_world @ v.co).z for v in mesh.vertices]
        return min(zs), max(zs)
    finally:
        oe.to_mesh_clear()

before = {n: z_bounds(get_obj(n)) for n in STACK}

# Sequentially enforce explicit geometric contact: upper bottom = lower top - EPS
adjustments = []
for lower_name, upper_name in zip(STACK[:-1], STACK[1:]):
    lower = get_obj(lower_name)
    upper = get_obj(upper_name)

    lower_min, lower_max = z_bounds(lower)
    upper_min, upper_max = z_bounds(upper)

    target_upper_min = lower_max - EPS
    dz = target_upper_min - upper_min
    upper.location.z += dz

    # force depsgraph refresh and measure after this joint adjustment
    bpy.context.view_layer.update()
    new_upper_min, new_upper_max = z_bounds(upper)
    new_lower_min, new_lower_max = z_bounds(lower)

    adjustments.append({
        'joint': f'{lower_name} -> {upper_name}',
        'before_lower_max': lower_max,
        'before_upper_min': upper_min,
        'before_gap': upper_min - lower_max,
        'applied_dz': dz,
        'after_lower_max': new_lower_max,
        'after_upper_min': new_upper_min,
        'after_gap': new_upper_min - new_lower_max,
        'overlap': new_lower_max - new_upper_min,
    })

after = {n: z_bounds(get_obj(n)) for n in STACK}

# Save .blend
bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)

# Export GLB
bpy.ops.export_scene.gltf(filepath=GLB_OUT, export_format='GLB')

# Render previews (3 wide + 1 detail)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.eevee.taa_render_samples = 16
cam = scene.camera
if cam is None:
    raise RuntimeError('Scene camera is missing')

target = bpy.data.objects.get('ChurchSpireV2') or bpy.data.objects.get('ChurchSpire')
center = Vector((0.0, 0.0, 6.5))
if target:
    center = target.location.copy()
    center.z = 6.5

radius = ((cam.location.x - center.x) ** 2 + (cam.location.y - center.y) ** 2) ** 0.5
if radius < 1:
    radius = 11.0
radius *= 1.55
look = center.copy()
look.z = 6.2

for i, ang in enumerate([35, 90, 145], start=1):
    rad = math.radians(ang)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    cam.location.z = center.z + 0.6
    d = look - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT_DIR, f'preview_v13_wide_{i}.png')
    bpy.ops.render.render(write_still=True)

# Detail close-up of top assembly
top_center = Vector((0.0, 0.0, (after['Cone.001'][1] + after['Cube.006'][1]) * 0.5))
detail_radius = max(1.6, radius * 0.22)
ang = math.radians(42)
cam.location.x = top_center.x + detail_radius * math.cos(ang)
cam.location.y = top_center.y + detail_radius * math.sin(ang)
cam.location.z = top_center.z + 0.35
look2 = top_center.copy()
look2.z = top_center.z - 0.05
cam.rotation_euler = (look2 - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = os.path.join(OUT_DIR, 'preview_v13_detail.png')
bpy.ops.render.render(write_still=True)

# Write notes
notes_path = os.path.join(OUT_DIR, 'FIX_NOTES_v13.md')
with open(notes_path, 'w', encoding='utf-8') as f:
    f.write('# Church Spire v13 — Hard Contact Fix Notes\n\n')
    f.write(f'Source: `assets/church_spire_v12/church_spire_v12.blend`\n\n')
    f.write('## Goal\n')
    f.write('Enforce explicit geometric contact in the top ornament stack by measuring world-space Z bounds and forcing a small intentional overlap at every joint.\n\n')
    f.write('## Overlap policy\n')
    f.write(f'- Target overlap epsilon: **{EPS:.3f} m** (upper min Z = lower max Z - epsilon).\n\n')
    f.write('## Measured joint contacts (world-space Z)\n\n')
    f.write('| Joint | Before lower max Z | Before upper min Z | Before gap (+) / overlap (-) | Applied ΔZ (upper) | After lower max Z | After upper min Z | After overlap |\n')
    f.write('|---|---:|---:|---:|---:|---:|---:|---:|\n')
    for a in adjustments:
        f.write(
            f"| {a['joint']} | {a['before_lower_max']:.4f} | {a['before_upper_min']:.4f} | {a['before_gap']:.4f} | {a['applied_dz']:.4f} | {a['after_lower_max']:.4f} | {a['after_upper_min']:.4f} | {a['overlap']:.4f} |\\n"
        )

    f.write('\n## Per-piece world Z bounds\n\n')
    f.write('| Piece | Before min Z | Before max Z | After min Z | After max Z |\n')
    f.write('|---|---:|---:|---:|---:|\n')
    for n in STACK:
        b0, b1 = before[n]
        a0, a1 = after[n]
        f.write(f'| {n} | {b0:.4f} | {b1:.4f} | {a0:.4f} | {a1:.4f} |\\n')

    f.write('\n## Outputs\n\n')
    f.write('- `church_spire_v13.blend`\n')
    f.write('- `church_spire_v13.glb`\n')
    f.write('- `preview_v13_wide_1.png`\n')
    f.write('- `preview_v13_wide_2.png`\n')
    f.write('- `preview_v13_wide_3.png`\n')
    f.write('- `preview_v13_detail.png`\n')
    f.write('- `FIX_NOTES_v13.md`\n')

print('DONE')
for a in adjustments:
    print(a)
print('OUT', OUT_DIR)
