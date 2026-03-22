import bpy
import math
import os
from mathutils import Vector


# -----------------------------
# Paths and render defaults
# -----------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(REPO_ROOT, 'assets', 'french_house_v2')
os.makedirs(OUT_DIR, exist_ok=True)

BLEND_PATH = os.path.join(OUT_DIR, 'french_house_v2.blend')
GLB_PATH = os.path.join(OUT_DIR, 'french_house_v2.glb')


# -----------------------------
# Reusable scene helpers
# -----------------------------
def reset_scene(width=1600, height=900, samples=32):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.eevee.taa_render_samples = samples
    return scene


def make_world_gradient(scene):
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
    sep = nodes.new('ShaderNodeSeparateXYZ')
    ramp = nodes.new('ShaderNodeValToRGB')

    cr = ramp.color_ramp
    cr.elements[0].position = 0.18
    cr.elements[0].color = (0.92, 0.95, 1.0, 1.0)
    cr.elements[1].position = 0.98
    cr.elements[1].color = (0.30, 0.44, 0.72, 1.0)

    bg.inputs['Strength'].default_value = 1.1

    links.new(coord.outputs['Generated'], sep.inputs['Vector'])
    links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bg.inputs['Color'])
    links.new(bg.outputs['Background'], out.inputs['Surface'])


def mat(name, base=(0.8, 0.8, 0.8, 1.0), rough=0.8, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = base
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    return m


def z_bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    zs = [p.z for p in pts]
    return min(zs), max(zs)


def assert_on_ground(primary_base_obj, objects, eps=1e-4):
    base_min, _ = z_bounds(primary_base_obj)
    if abs(base_min) > eps:
        raise RuntimeError(f'Base grounding check failed: {primary_base_obj.name} min_z={base_min:.5f}')

    below = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        min_z, _ = z_bounds(obj)
        if min_z < -eps:
            below.append((obj.name, min_z))
    if below:
        details = '\n'.join([f'- {n}: min_z={z:.5f}' for n, z in below])
        raise RuntimeError(f'Ground intersection check failed (below ground):\n{details}')


def assert_roof_over_walls(roof_obj, wall_obj, allowed_embed=0.35):
    wall_min, wall_max = z_bounds(wall_obj)
    roof_min, roof_max = z_bounds(roof_obj)
    if roof_min < wall_max - allowed_embed:
        raise RuntimeError(
            f'Roof-wall check failed: roof embeds too deep (roof_min={roof_min:.3f}, wall_max={wall_max:.3f}, allowed_embed={allowed_embed:.3f})'
        )
    if roof_min > wall_max + 0.12:
        raise RuntimeError(
            f'Roof-wall check failed: visible gap between roof and walls (roof_min={roof_min:.3f}, wall_max={wall_max:.3f})'
        )
    if roof_max <= wall_max:
        raise RuntimeError('Roof silhouette check failed: roof does not rise above wall massing')


# -----------------------------
# Build asset
# -----------------------------
scene = reset_scene()
make_world_gradient(scene)

# Materials
m_stone = mat('StoneWallV2', base=(0.69, 0.66, 0.60, 1.0), rough=0.93)
m_plaster = mat('PlasterV2', base=(0.82, 0.78, 0.70, 1.0), rough=0.88)
m_timber = mat('TimberV2', base=(0.33, 0.22, 0.15, 1.0), rough=0.86)
m_thatch = mat('ThatchV2', base=(0.60, 0.49, 0.25, 1.0), rough=0.95)
m_door = mat('DoorWoodV2', base=(0.24, 0.15, 0.10, 1.0), rough=0.7)
m_window = mat('WindowFrameV2', base=(0.18, 0.21, 0.23, 1.0), rough=0.52)
m_ground = mat('GroundV2', base=(0.35, 0.46, 0.30, 1.0), rough=0.97)

meshes = []
building_parts = []

# Ground
bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, 0))
ground = bpy.context.active_object
ground.data.materials.append(m_ground)
meshes.append(ground)

# Main body (stone base)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1.2))
base = bpy.context.active_object
base.scale = (2.6, 1.9, 1.2)
bev = base.modifiers.new('Bevel', 'BEVEL')
bev.width = 0.06
bev.segments = 2
base.data.materials.append(m_stone)
meshes.append(base)
building_parts.append(base)

# Upper body (plaster)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 3.0))
upper = bpy.context.active_object
upper.scale = (2.35, 1.65, 0.72)
upper.data.materials.append(m_plaster)
meshes.append(upper)
building_parts.append(upper)

# Roof rotated 90° around Z from v1 to swap ridge axis orientation
bpy.ops.mesh.primitive_cone_add(
    vertices=4,
    radius1=3.25,
    radius2=0.22,
    depth=2.8,
    location=(0, 0, 4.75),
    rotation=(0, 0, math.radians(135)),
)
roof = bpy.context.active_object
roof.data.materials.append(m_thatch)
meshes.append(roof)
building_parts.append(roof)

# Roof ridge cap axis swapped (Y -> X)
bpy.ops.mesh.primitive_cylinder_add(
    vertices=8,
    radius=0.12,
    depth=4.8,
    location=(0, 0, 5.48),
    rotation=(0, math.radians(90), 0),
)
ridge = bpy.context.active_object
ridge.data.materials.append(m_thatch)
meshes.append(ridge)
building_parts.append(ridge)

# Chimney
bpy.ops.mesh.primitive_cube_add(size=1, location=(1.15, 0.25, 4.65))
chim = bpy.context.active_object
chim.scale = (0.22, 0.22, 0.75)
chim.data.materials.append(m_stone)
meshes.append(chim)
building_parts.append(chim)

# Timber corner accents
for x in (-2.35, 2.35):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -1.56, 2.28))
    t = bpy.context.active_object
    t.scale = (0.06, 0.06, 1.45)
    t.data.materials.append(m_timber)
    meshes.append(t)
    building_parts.append(t)

# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, -1.93, 0.92))
door = bpy.context.active_object
door.scale = (0.42, 0.06, 0.92)
door.data.materials.append(m_door)
meshes.append(door)
building_parts.append(door)

# Windows front/back (stylized)
for y, rot in [(-1.93, 0.0), (1.93, math.pi)]:
    for x in (-1.2, 1.2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 1.6), rotation=(0, 0, rot))
        w = bpy.context.active_object
        w.scale = (0.28, 0.05, 0.34)
        w.data.materials.append(m_window)
        meshes.append(w)
        building_parts.append(w)

# Side dormer-ish tiny windows
for y in (-0.65, 0.65):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(2.42, y, 3.12), rotation=(0, 0, math.radians(90)))
    w = bpy.context.active_object
    w.scale = (0.2, 0.05, 0.2)
    w.data.materials.append(m_window)
    meshes.append(w)
    building_parts.append(w)

# Parent
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
root = bpy.context.active_object
root.name = 'FrenchHouseV2'
for obj in building_parts:
    obj.parent = root

# Checks
assert_on_ground(base, building_parts)
assert_roof_over_walls(roof, upper, allowed_embed=0.45)

# Lighting
for o in list(scene.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.light_add(type='SUN', location=(7, -9, 14))
sun = bpy.context.active_object
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(48), math.radians(4), math.radians(28))

bpy.ops.object.light_add(type='AREA', location=(-5.5, 5.5, 4.5))
fill = bpy.context.active_object
fill.data.energy = 180
fill.data.size = 6
fill.rotation_euler = (math.radians(78), 0, math.radians(-35))

# Save .blend
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# Export GLB (exclude ground plane)
bpy.ops.object.select_all(action='DESELECT')
for o in building_parts:
    o.select_set(True)
root.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB', use_selection=True)

print('DONE french_house_v2')
print('BLEND', BLEND_PATH)
print('GLB', GLB_PATH)
