import bpy
import math
import os
from mathutils import Vector

OUT_DIR = "/home/azureuser/.openclaw/workspace/assets/church_spire_v2"
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

if scene.world is None:
    scene.world = bpy.data.worlds.new('World')
world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs[0].default_value = (0.93, 0.95, 1.0, 1.0)
bg.inputs[1].default_value = 0.95

# Materials
stone = bpy.data.materials.new(name='Stone')
stone.use_nodes = True
s = stone.node_tree.nodes['Principled BSDF']
s.inputs['Base Color'].default_value = (0.64, 0.66, 0.70, 1)
s.inputs['Roughness'].default_value = 0.88

roof = bpy.data.materials.new(name='Roof')
roof.use_nodes = True
r = roof.node_tree.nodes['Principled BSDF']
r.inputs['Base Color'].default_value = (0.24, 0.25, 0.29, 1)
r.inputs['Roughness'].default_value = 0.72

metal = bpy.data.materials.new(name='Metal')
metal.use_nodes = True
m = metal.node_tree.nodes['Principled BSDF']
m.inputs['Base Color'].default_value = (0.75, 0.71, 0.56, 1)
m.inputs['Metallic'].default_value = 0.65
m.inputs['Roughness'].default_value = 0.35

window_mat = bpy.data.materials.new(name='WindowGlass')
window_mat.use_nodes = True
w = window_mat.node_tree.nodes['Principled BSDF']
w.inputs['Base Color'].default_value = (0.22, 0.30, 0.40, 1)
w.inputs['Transmission Weight'].default_value = 0.75
w.inputs['Roughness'].default_value = 0.08

# Geometry: taller spire body + shorter tip
bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,3.2))
tower = bpy.context.active_object
tower.scale = (1.55, 1.55, 3.2)  # taller body

a = tower.modifiers.new('Bevel', 'BEVEL')
a.width = 0.03
a.segments = 2

bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,6.95))
upper = bpy.context.active_object
upper.scale = (1.22, 1.22, 0.95)

bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.22, radius2=0.86, depth=1.65, location=(0,0,8.4))
roof_lower = bpy.context.active_object

bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.92, radius2=0.18, depth=3.0, location=(0,0,10.75))  # shorter tip
spire = bpy.context.active_object

# Finial + cross
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.11, location=(0,0,12.38))
finial_ball = bpy.context.active_object

bpy.ops.mesh.primitive_cube_add(size=0.08, location=(0,0,12.66))
cross_v = bpy.context.active_object
cross_v.scale = (0.35, 0.35, 2.5)

bpy.ops.mesh.primitive_cube_add(size=0.08, location=(0,0,12.66))
cross_h = bpy.context.active_object
cross_h.scale = (1.95, 0.35, 0.35)

# Windows: simple arched-ish vertical windows on four sides
window_objs = []
for z in [2.2, 3.5, 4.8, 6.0]:
    for x, y, rot in [(1.57,0,0), (-1.57,0,math.pi), (0,1.57,-math.pi/2), (0,-1.57,math.pi/2)]:
        bpy.ops.mesh.primitive_cube_add(size=0.32, location=(x,y,z), rotation=(0,0,rot))
        wo = bpy.context.active_object
        wo.scale = (0.12, 0.02, 0.34)
        window_objs.append(wo)

# Buttresses
for sx, sy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
    bpy.ops.mesh.primitive_cube_add(size=0.72, location=(sx*1.58, sy*1.58, 1.4))
    b = bpy.context.active_object
    b.scale = (0.34, 0.34, 1.35)

# Ground
bpy.ops.mesh.primitive_plane_add(size=22, location=(0,0,0))
ground = bpy.context.active_object

# Assign materials
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    if obj in [spire, roof_lower]:
        obj.data.materials.append(roof)
    elif obj in [finial_ball, cross_v, cross_h]:
        obj.data.materials.append(metal)
    elif obj in window_objs:
        obj.data.materials.append(window_mat)
    elif obj == ground:
        gm = bpy.data.materials.new(name='Ground')
        gm.use_nodes = True
        gbsdf = gm.node_tree.nodes['Principled BSDF']
        gbsdf.inputs['Base Color'].default_value = (0.88,0.89,0.9,1)
        gbsdf.inputs['Roughness'].default_value = 0.96
        obj.data.materials.append(gm)
    else:
        obj.data.materials.append(stone)

# Parent to root
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
root = bpy.context.active_object
root.name = 'ChurchSpireV2'
for obj in list(scene.objects):
    if obj.type == 'MESH' and obj != ground:
        obj.parent = root

# Camera framing from bounds
pts = []
for obj in scene.objects:
    if obj.type != 'MESH' or obj == ground:
        continue
    for c in obj.bound_box:
        pts.append(obj.matrix_world @ Vector(c))

min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (min_v + max_v) * 0.5
height = max_v.z - min_v.z

bpy.ops.object.camera_add(location=(0,-18,center.z), rotation=(math.radians(85),0,0))
cam = bpy.context.active_object
scene.camera = cam

fov = cam.data.angle_y
half_h = (height * 0.5) * 1.18
radius = (half_h / math.tan(fov * 0.5)) * 1.3

# Light
bpy.ops.object.light_add(type='SUN', location=(4,-5,14))
sun = bpy.context.active_object
sun.data.energy = 4.2
sun.rotation_euler = (math.radians(42), math.radians(8), math.radians(32))

angles = [35, 90, 145]
for i, a in enumerate(angles, start=1):
    rad = math.radians(a)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    cam.location.z = center.z
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT_DIR, f'preview_v2_{i}.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, 'church_spire_v2.blend'))

# export
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, 'church_spire_v2.glb'), export_format='GLB', use_selection=True)

print('DONE', OUT_DIR)
