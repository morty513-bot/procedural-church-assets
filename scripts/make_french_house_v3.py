import bpy
import bmesh
import math
import os
from mathutils import Vector


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(REPO_ROOT, 'assets', 'french_house_v3')
os.makedirs(OUT_DIR, exist_ok=True)

BLEND_PATH = os.path.join(OUT_DIR, 'french_house_v3.blend')
GLB_PATH = os.path.join(OUT_DIR, 'french_house_v3.glb')


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


def xy_bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


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


def assert_centered_xy(a, b, tol=0.04):
    ax0, ax1, ay0, ay1 = xy_bounds(a)
    bx0, bx1, by0, by1 = xy_bounds(b)
    ac = ((ax0 + ax1) * 0.5, (ay0 + ay1) * 0.5)
    bc = ((bx0 + bx1) * 0.5, (by0 + by1) * 0.5)
    if abs(ac[0] - bc[0]) > tol or abs(ac[1] - bc[1]) > tol:
        raise RuntimeError(
            f'Massing alignment failed: centers diverge a={ac}, b={bc}, tol={tol}'
        )


def assert_roof_overhang_consistent(roof_obj, wall_obj, target_x=0.28, target_y=0.24, tol=0.06):
    rx0, rx1, ry0, ry1 = xy_bounds(roof_obj)
    wx0, wx1, wy0, wy1 = xy_bounds(wall_obj)

    ox_l = wx0 - rx0
    ox_r = rx1 - wx1
    oy_f = wy0 - ry0
    oy_b = ry1 - wy1

    if max(abs(ox_l - ox_r), abs(oy_f - oy_b)) > tol:
        raise RuntimeError(
            f'Roof overhang symmetry failed x=({ox_l:.3f},{ox_r:.3f}) y=({oy_f:.3f},{oy_b:.3f})'
        )
    if abs(((ox_l + ox_r) * 0.5) - target_x) > tol or abs(((oy_f + oy_b) * 0.5) - target_y) > tol:
        raise RuntimeError(
            f'Roof overhang target drift x~{(ox_l+ox_r)*0.5:.3f} y~{(oy_f+oy_b)*0.5:.3f} '
            f'expected x={target_x:.3f} y={target_y:.3f}'
        )


def assert_roof_seating(roof_obj, wall_obj, min_embed=0.05, max_embed=0.24):
    _, wall_top = z_bounds(wall_obj)
    roof_min, roof_max = z_bounds(roof_obj)
    embed = wall_top - roof_min
    if embed < min_embed or embed > max_embed:
        raise RuntimeError(
            f'Roof seating failed: embed={embed:.3f} (wall_top={wall_top:.3f}, roof_min={roof_min:.3f})'
        )
    if roof_max <= wall_top:
        raise RuntimeError('Roof silhouette failed: roof does not rise above wall massing')


def assert_chimney_embedded(chim_obj, roof_surface_z_at_chim, min_embed=0.12):
    chim_min, _ = z_bounds(chim_obj)
    if roof_surface_z_at_chim - chim_min < min_embed:
        raise RuntimeError(
            f'Chimney embed failed: roof_z={roof_surface_z_at_chim:.3f} chim_min={chim_min:.3f}'
        )


def create_gable_roof(name, width_x, depth_y, rise_z):
    mesh = bpy.data.meshes.new(name + 'Mesh')
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hx = width_x * 0.5
    hy = depth_y * 0.5

    v0 = bm.verts.new((-hx, -hy, 0.0))
    v1 = bm.verts.new((hx, -hy, 0.0))
    v2 = bm.verts.new((-hx, hy, 0.0))
    v3 = bm.verts.new((hx, hy, 0.0))
    v4 = bm.verts.new((-hx, 0.0, rise_z))
    v5 = bm.verts.new((hx, 0.0, rise_z))

    bm.faces.new((v0, v1, v5, v4))
    bm.faces.new((v2, v3, v5, v4))
    bm.faces.new((v0, v2, v4))
    bm.faces.new((v1, v3, v5))
    bm.faces.new((v0, v1, v3, v2))

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    bev = obj.modifiers.new('RoofBevel', 'BEVEL')
    bev.width = 0.03
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    return obj


scene = reset_scene()
make_world_gradient(scene)

m_stone = mat('StoneWallV3', base=(0.69, 0.66, 0.60, 1.0), rough=0.93)
m_plaster = mat('PlasterV3', base=(0.82, 0.78, 0.70, 1.0), rough=0.88)
m_timber = mat('TimberV3', base=(0.33, 0.22, 0.15, 1.0), rough=0.86)
m_thatch = mat('ThatchV3', base=(0.60, 0.49, 0.25, 1.0), rough=0.95)
m_door = mat('DoorWoodV3', base=(0.24, 0.15, 0.10, 1.0), rough=0.7)
m_window = mat('WindowFrameV3', base=(0.18, 0.21, 0.23, 1.0), rough=0.52)
m_ground = mat('GroundV3', base=(0.35, 0.46, 0.30, 1.0), rough=0.97)

meshes = []
building_parts = []

bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = 'Ground'
ground.data.materials.append(m_ground)
meshes.append(ground)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1.2))
base = bpy.context.active_object
base.name = 'BaseMass'
base.scale = (2.6, 1.9, 1.2)
bev = base.modifiers.new('Bevel', 'BEVEL')
bev.width = 0.06
bev.segments = 2
base.data.materials.append(m_stone)
meshes.append(base)
building_parts.append(base)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 3.0))
upper = bpy.context.active_object
upper.name = 'UpperMass'
upper.scale = (2.35, 1.65, 0.72)
upper.data.materials.append(m_plaster)
meshes.append(upper)
building_parts.append(upper)

roof_width_x = upper.scale.x * 2 + 0.56
roof_depth_y = upper.scale.y * 2 + 0.48
roof_rise_z = 1.60
roof_base_z = 3.55
roof = create_gable_roof('Roof', roof_width_x, roof_depth_y, roof_rise_z)
roof.location = (0, 0, roof_base_z)
roof.data.materials.append(m_thatch)
meshes.append(roof)
building_parts.append(roof)

bpy.ops.mesh.primitive_cylinder_add(
    vertices=10,
    radius=0.09,
    depth=roof_width_x * 0.98,
    location=(0, 0, roof_base_z + roof_rise_z + 0.04),
    rotation=(0, math.radians(90), 0),
)
ridge = bpy.context.active_object
ridge.name = 'RoofRidgeCap'
ridge.data.materials.append(m_thatch)
meshes.append(ridge)
building_parts.append(ridge)

pitch = math.atan2(roof_rise_z, (roof_depth_y * 0.5))
chim_x = 1.05
chim_y = 0.72
roof_surface_z = roof_base_z + roof_rise_z * (1.0 - abs(chim_y) / (roof_depth_y * 0.5))
chim_bottom = roof_surface_z - 0.48
chim_height = 1.26

bpy.ops.mesh.primitive_cube_add(size=1, location=(chim_x, chim_y, chim_bottom + chim_height * 0.5))
chim = bpy.context.active_object
chim.name = 'Chimney'
chim.scale = (0.20, 0.18, chim_height * 0.5)
chim.data.materials.append(m_stone)
meshes.append(chim)
building_parts.append(chim)

bpy.ops.mesh.primitive_cylinder_add(
    vertices=12,
    radius=0.045,
    depth=0.68,
    location=(chim_x + 0.02, chim_y + 0.02, chim_bottom + chim_height + 0.30),
    rotation=(-pitch * 0.35, 0, 0),
)
flue = bpy.context.active_object
flue.name = 'ChimneyFlue'
flue.data.materials.append(m_window)
meshes.append(flue)
building_parts.append(flue)

for x in (-2.35, 2.35):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -1.56, 2.28))
    t = bpy.context.active_object
    t.scale = (0.06, 0.06, 1.45)
    t.data.materials.append(m_timber)
    meshes.append(t)
    building_parts.append(t)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, -1.93, 0.92))
door = bpy.context.active_object
door.scale = (0.42, 0.06, 0.92)
door.data.materials.append(m_door)
meshes.append(door)
building_parts.append(door)

for y, rot in [(-1.93, 0.0), (1.93, math.pi)]:
    for x in (-1.2, 1.2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 1.6), rotation=(0, 0, rot))
        w = bpy.context.active_object
        w.scale = (0.28, 0.05, 0.34)
        w.data.materials.append(m_window)
        meshes.append(w)
        building_parts.append(w)

for y in (-0.65, 0.65):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(2.42, y, 3.12), rotation=(0, 0, math.radians(90)))
    w = bpy.context.active_object
    w.scale = (0.2, 0.05, 0.2)
    w.data.materials.append(m_window)
    meshes.append(w)
    building_parts.append(w)

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
root = bpy.context.active_object
root.name = 'FrenchHouseV3'
for obj in building_parts:
    obj.parent = root

assert_on_ground(base, building_parts)
assert_centered_xy(base, upper, tol=0.02)
assert_centered_xy(upper, roof, tol=0.03)
assert_roof_overhang_consistent(roof, upper, target_x=0.31, target_y=0.30, tol=0.06)
assert_roof_seating(roof, upper, min_embed=0.08, max_embed=0.22)
assert_chimney_embedded(chim, roof_surface_z, min_embed=0.14)

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

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

bpy.ops.object.select_all(action='DESELECT')
for o in building_parts:
    o.select_set(True)
root.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB', use_selection=True)

print('DONE french_house_v3')
print('BLEND', BLEND_PATH)
print('GLB', GLB_PATH)
