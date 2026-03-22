import bpy
import math
import os
from mathutils import Vector

OUT_DIR = "/home/azureuser/.openclaw/workspace/assets/church_spire_v10"
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.eevee.taa_render_samples = 32

# -----------------------------
# Stable world-space Z gradient sky (vivid fantasy palette)
# -----------------------------
if scene.world is None:
    scene.world = bpy.data.worlds.new('World')
world = scene.world
world.use_nodes = True
nt = world.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()

out = nodes.new('ShaderNodeOutputWorld')
bg = nodes.new('ShaderNodeBackground')
coord = nodes.new('ShaderNodeTexCoord')
separate = nodes.new('ShaderNodeSeparateXYZ')
map_range = nodes.new('ShaderNodeMapRange')
ramp = nodes.new('ShaderNodeValToRGB')

map_range.inputs['From Min'].default_value = -1.0
map_range.inputs['From Max'].default_value = 1.0
map_range.inputs['To Min'].default_value = 0.0
map_range.inputs['To Max'].default_value = 1.0
map_range.clamp = True

cr = ramp.color_ramp
cr.elements[0].position = 0.12
cr.elements[0].color = (1.00, 0.55, 0.20, 1.0)
cr.elements[1].position = 0.98
cr.elements[1].color = (0.08, 0.14, 0.50, 1.0)
mid = cr.elements.new(0.52)
mid.color = (0.86, 0.29, 0.62, 1.0)
bg.inputs['Strength'].default_value = 1.2

links.new(coord.outputs['Generated'], separate.inputs['Vector'])
links.new(separate.outputs['Z'], map_range.inputs['Value'])
links.new(map_range.outputs['Result'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bg.inputs['Color'])
links.new(bg.outputs['Background'], out.inputs['Surface'])

# -----------------------------
# Materials (clear differentiation)
# -----------------------------
def make_mat(name, base=(0.8, 0.8, 0.8, 1), rough=0.8, metallic=0.0, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = base
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = emission
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    return m

stone = make_mat('StoneV10', base=(0.74, 0.69, 0.59, 1), rough=0.93)
stone_dark = make_mat('StoneDarkV10', base=(0.56, 0.50, 0.43, 1), rough=0.96)
slate_roof = make_mat('SlateRoofV10', base=(0.08, 0.10, 0.19, 1), rough=0.62)
window_glow = make_mat('WindowGlowV10', base=(0.06, 0.40, 0.55, 1), rough=0.05, emission=(0.18, 0.85, 1.0, 1), emission_strength=2.8)
metal = make_mat('FinialMetalV10', base=(0.92, 0.76, 0.30, 1), rough=0.22, metallic=0.95)
accent = make_mat('AccentTerracottaV10', base=(0.58, 0.24, 0.16, 1), rough=0.8)

# -----------------------------
# Geometry: stylized Saint-Emilion-inspired spire/tower
# -----------------------------
objects_for_export = []
window_objs = []

# Ground
bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, 0))
ground = bpy.context.active_object
objects_for_export.append(ground)

ground_mat = bpy.data.materials.new('GroundGrassV10')
ground_mat.use_nodes = True
gbsdf = ground_mat.node_tree.nodes['Principled BSDF']
gbsdf.inputs['Base Color'].default_value = (0.26, 0.47, 0.25, 1)
gbsdf.inputs['Roughness'].default_value = 0.95
ground.data.materials.append(ground_mat)

# Main tower massing
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 3.2))
base = bpy.context.active_object
base.scale = (1.95, 1.95, 3.2)
objects_for_export.append(base)

bev = base.modifiers.new('Bevel', 'BEVEL')
bev.width = 0.06
bev.segments = 2

# Buttress-like corner masses
for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
    bpy.ops.mesh.primitive_cube_add(size=0.9, location=(sx * 1.85, sy * 1.85, 1.55))
    b = bpy.context.active_object
    b.scale = (0.36, 0.36, 1.55)
    objects_for_export.append(b)

# Belfry stage (octagonal)
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.45, depth=2.2, location=(0, 0, 8.25))
belfry = bpy.context.active_object
objects_for_export.append(belfry)

# Transition roof 1: broader skirt
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.58, radius2=1.02, depth=1.3, location=(0, 0, 9.95))
roof_skirt = bpy.context.active_object
objects_for_export.append(roof_skirt)

# Transition roof 2: steeper upper spire
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.02, radius2=0.22, depth=5.0, location=(0, 0, 12.95))
spire = bpy.context.active_object
objects_for_export.append(spire)

# Lantern/ornamental collar near top
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.30, depth=0.28, location=(0, 0, 15.55))
collar = bpy.context.active_object
objects_for_export.append(collar)

# Finial: sphere + cross
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.13, location=(0, 0, 15.85))
finial_ball = bpy.context.active_object
objects_for_export.append(finial_ball)

bpy.ops.mesh.primitive_cube_add(size=0.09, location=(0, 0, 16.12))
cross_v = bpy.context.active_object
cross_v.scale = (0.30, 0.30, 2.5)
objects_for_export.append(cross_v)

bpy.ops.mesh.primitive_cube_add(size=0.09, location=(0, 0, 16.12))
cross_h = bpy.context.active_object
cross_h.scale = (1.8, 0.30, 0.30)
objects_for_export.append(cross_h)

# Small crockets / pinnacles around lower upper roof ring
for i in range(8):
    ang = (math.pi * 2.0 * i) / 8.0
    r = 1.28
    x, y = r * math.cos(ang), r * math.sin(ang)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.08, radius2=0.0, depth=0.38, location=(x, y, 10.45))
    pin = bpy.context.active_object
    pin.rotation_euler[2] = ang
    objects_for_export.append(pin)

# Belfry openings (readable lancet-like void proxies)
for i in range(8):
    ang = (math.pi * 2.0 * i) / 8.0
    r = 1.33
    x, y = r * math.cos(ang), r * math.sin(ang)
    bpy.ops.mesh.primitive_cube_add(size=0.48, location=(x, y, 8.15))
    w = bpy.context.active_object
    w.scale = (0.24, 0.045, 0.62)
    w.rotation_euler = (0, 0, ang)
    window_objs.append(w)
    objects_for_export.append(w)

# Mid-level narrow slit windows
for z in [3.0, 4.4, 5.8]:
    for x, y, rot in [(1.98, 0, 0), (-1.98, 0, math.pi), (0, 1.98, -math.pi/2), (0, -1.98, math.pi/2)]:
        bpy.ops.mesh.primitive_cube_add(size=0.36, location=(x, y, z), rotation=(0, 0, rot))
        w = bpy.context.active_object
        w.scale = (0.13, 0.03, 0.48)
        window_objs.append(w)
        objects_for_export.append(w)

# -----------------------------
# Material assignment
# -----------------------------
roof_set = {roof_skirt.name, spire.name}
metal_set = {finial_ball.name, cross_v.name, cross_h.name, collar.name}
accent_set = set()
for o in scene.objects:
    if o.type != 'MESH':
        continue
    o.data.materials.clear()
    if o == ground:
        # already has material
        continue
    if o in window_objs:
        o.data.materials.append(window_glow)
    elif o.name in roof_set:
        o.data.materials.append(slate_roof)
    elif o.name in metal_set:
        o.data.materials.append(metal)
    elif o.dimensions.x < 0.4 and o.location.z > 10.2:
        o.data.materials.append(accent)
        accent_set.add(o.name)
    elif o == belfry:
        o.data.materials.append(stone_dark)
    else:
        o.data.materials.append(stone)

# Parent objects for tidy export
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
root = bpy.context.active_object
root.name = 'ChurchSpireV10'
for o in objects_for_export:
    if o != ground:
        o.parent = root

# -----------------------------
# Lighting / camera
# -----------------------------
for o in list(scene.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.light_add(type='SUN', location=(8, -9, 16))
sun = bpy.context.active_object
sun.data.energy = 3.8
sun.rotation_euler = (math.radians(46), math.radians(7), math.radians(26))

bpy.ops.object.light_add(type='AREA', location=(-7, 6, 8))
fill = bpy.context.active_object
fill.data.energy = 260
fill.data.size = 8
fill.rotation_euler = (math.radians(80), 0, math.radians(-34))

# Compute center from bounds (excluding ground)
pts = []
for o in scene.objects:
    if o.type != 'MESH' or o == ground:
        continue
    for c in o.bound_box:
        pts.append(o.matrix_world @ Vector(c))

min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (min_v + max_v) * 0.5
center.z = 7.2
height = max_v.z - min_v.z

bpy.ops.object.camera_add(location=(0, -14, center.z))
cam = bpy.context.active_object
scene.camera = cam

fov = cam.data.angle_y
half_h = (height * 0.5) * 1.08
radius = (half_h / max(math.tan(fov * 0.5), 0.01)) * 1.08
radius = max(radius, 10.5)

# Three standard preview angles (aligned with earlier workflow)
for i, ang in enumerate([35, 90, 145], start=1):
    rad = math.radians(ang)
    cam.location.x = center.x + radius * math.cos(rad)
    cam.location.y = center.y + radius * math.sin(rad)
    cam.location.z = center.z
    d = center - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT_DIR, f'preview_v10_{i}.png')
    bpy.ops.render.render(write_still=True)

# Detail shot (closer, focused on belfry + roof transition)
focus = Vector((0, 0, 10.1))
ang = math.radians(28)
cam.location = Vector((6.0 * math.cos(ang), 6.0 * math.sin(ang), 10.35))
cam.rotation_euler = (focus - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = os.path.join(OUT_DIR, 'preview_v10_detail.png')
bpy.ops.render.render(write_still=True)

# Save and export
blend_path = os.path.join(OUT_DIR, 'church_spire_v10.blend')
glb_path = os.path.join(OUT_DIR, 'church_spire_v10.glb')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

bpy.ops.object.select_all(action='DESELECT')
for o in objects_for_export:
    if o != ground:
        o.select_set(True)
root.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', use_selection=True)

print('DONE', OUT_DIR)
