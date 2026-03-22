import bpy, os, math
from mathutils import Vector

SRC='/home/azureuser/.openclaw/workspace/assets/church_spire_v14/church_spire_v14.blend'
OUT='/home/azureuser/.openclaw/workspace/assets/church_spire_v15'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.eevee.taa_render_samples=16

# Helpers

def world_bounds_z(obj):
    pts=[obj.matrix_world @ Vector(c) for c in obj.bound_box]
    zs=[p.z for p in pts]
    return min(zs), max(zs)

def center_xy(obj):
    return (obj.matrix_world.translation.x, obj.matrix_world.translation.y)

# Pick central stack objects only (exclude side pinnacles/windows)
candidates=[]
for o in scene.objects:
    if o.type!='MESH':
        continue
    if o.name.lower()=='plane':
        continue
    x,y=center_xy(o)
    # near center axis only
    if abs(x) <= 0.5 and abs(y) <= 0.5:
        mn,mx=world_bounds_z(o)
        candidates.append((o,mn,mx))

# Sort by minZ ascending and enforce no-gap stack with tiny overlap
candidates.sort(key=lambda t: t[1])
eps=0.015

for i in range(len(candidates)-1):
    lower, lmin, lmax = candidates[i]
    upper, umin, umax = candidates[i+1]
    desired_umin = lmax - eps
    dz = desired_umin - umin
    if abs(dz) > 1e-6:
        upper.location.z += dz
        # refresh this and all later cached bounds
        for j in range(i+1, len(candidates)):
            o,_,_ = candidates[j]
            mn,mx = world_bounds_z(o)
            candidates[j] = (o,mn,mx)

# Wide framing from object bounds (guarantee full model visible)
all_pts=[]
for o in scene.objects:
    if o.type!='MESH' or o.name.lower()=='plane':
        continue
    for c in o.bound_box:
        all_pts.append(o.matrix_world @ Vector(c))
min_v=Vector((min(p.x for p in all_pts), min(p.y for p in all_pts), min(p.z for p in all_pts)))
max_v=Vector((max(p.x for p in all_pts), max(p.y for p in all_pts), max(p.z for p in all_pts)))
center=(min_v+max_v)*0.5
height=max_v.z-min_v.z

cam=scene.camera
if cam is None:
    bpy.ops.object.camera_add()
    cam=bpy.context.active_object
    scene.camera=cam

# Use FOV to pick distance with generous margin
fov = cam.data.angle_y
half_h = (height * 0.5) * 1.35
radius = (half_h / max(math.tan(fov*0.5), 1e-3)) * 1.35
look=center.copy(); look.z = center.z

angles=[35,90,145]
for i,a in enumerate(angles, start=1):
    rad=math.radians(a)
    cam.location.x = center.x + radius*math.cos(rad)
    cam.location.y = center.y + radius*math.sin(rad)
    cam.location.z = center.z + 0.6
    d = look - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'preview_v15_wide_{i}.png')
    bpy.ops.render.render(write_still=True)

# Detail shot (still include top and joint area)
cam.location = Vector((center.x + radius*0.65, center.y - radius*0.65, center.z + height*0.15))
d = (center + Vector((0,0,height*0.18))) - cam.location
cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
scene.render.filepath = os.path.join(OUT, 'preview_v15_detail.png')
bpy.ops.render.render(write_still=True)

# Save / export
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v15.blend'))

# Export GLB for full scene meshes except ground via selection
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type=='MESH' and o.name.lower()!='plane':
        o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'church_spire_v15.glb'), export_format='GLB', use_selection=True)

# Write quick proof log
with open(os.path.join(OUT,'FIX_NOTES_v15.md'),'w') as f:
    f.write('# v15 immediate fix\n')
    f.write('- Fixed central stack to remove gaps using world-space min/max Z contact constraints.\n')
    f.write(f'- Overlap epsilon: {eps} m\n')
    f.write('- Rendered wider camera framing to show full spire.\n\n')
    f.write('## Central stack after fix (minZ -> maxZ)\n')
    for o,mn,mx in candidates:
        f.write(f'- {o.name}: {mn:.4f} -> {mx:.4f}\n')

print('DONE', OUT)
