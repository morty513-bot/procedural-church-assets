import bpy
import bmesh
import math
import os

OUT_DIR = "/home/mainuser/.openclaw/workspace/assets/church_spire"
os.makedirs(OUT_DIR, exist_ok=True)

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.film_transparent = False

# Simple world light
if scene.world is None:
    scene.world = bpy.data.worlds.new('World')
world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs[0].default_value = (0.92, 0.94, 1.0, 1.0)
bg.inputs[1].default_value = 0.9

# Helpers

def shade_flat(obj):
    mesh = obj.data
    for p in mesh.polygons:
        p.use_smooth = False

# Materials
stone = bpy.data.materials.new(name='Stone')
stone.use_nodes = True
bsdf = stone.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (0.62, 0.64, 0.67, 1)
bsdf.inputs['Roughness'].default_value = 0.85

roof = bpy.data.materials.new(name='Roof')
roof.use_nodes = True
bsdf2 = roof.node_tree.nodes.get('Principled BSDF')
bsdf2.inputs['Base Color'].default_value = (0.24, 0.26, 0.30, 1)
bsdf2.inputs['Roughness'].default_value = 0.7

metal = bpy.data.materials.new(name='Metal')
metal.use_nodes = True
bsdf3 = metal.node_tree.nodes.get('Principled BSDF')
bsdf3.inputs['Base Color'].default_value = (0.75, 0.70, 0.55, 1)
bsdf3.inputs['Metallic'].default_value = 0.7
bsdf3.inputs['Roughness'].default_value = 0.3

# Base tower
bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,2.2))
tower = bpy.context.active_object
tower.name = "Spire_Tower"
tower.scale = (1.5, 1.5, 2.2)
shade_flat(tower)

# Slight taper top section
bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,5.05))
upper = bpy.context.active_object
upper.name = "Spire_Upper"
upper.scale = (1.2, 1.2, 0.65)
shade_flat(upper)

# Octagonal roof / spire lower
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.25, radius2=0.7, depth=1.9, location=(0,0,6.35))
roof_lower = bpy.context.active_object
roof_lower.name = "Spire_RoofLower"
shade_flat(roof_lower)

# Main spire
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.78, radius2=0.05, depth=4.8, location=(0,0,9.7))
spire = bpy.context.active_object
spire.name = "Spire_Main"
shade_flat(spire)

# Finial sphere + cross
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.12, location=(0,0,12.15))
finial_ball = bpy.context.active_object
finial_ball.name = "Spire_FinialBall"
shade_flat(finial_ball)

bpy.ops.mesh.primitive_cube_add(size=0.08, location=(0,0,12.45))
cross_vert = bpy.context.active_object
cross_vert.scale = (0.35, 0.35, 3.2)
shade_flat(cross_vert)

bpy.ops.mesh.primitive_cube_add(size=0.08, location=(0,0,12.46))
cross_horiz = bpy.context.active_object
cross_horiz.scale = (2.2, 0.35, 0.35)
shade_flat(cross_horiz)

# Add minimal buttresses for silhouette
for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
    bpy.ops.mesh.primitive_cube_add(size=0.7, location=(sx*1.55, sy*1.55, 1.2))
    b = bpy.context.active_object
    b.scale = (0.35, 0.35, 1.15)
    shade_flat(b)

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
plane = bpy.context.active_object
plane.name = "Ground"

# Assign materials
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    if obj.name.startswith("Spire_Roof") or obj.name.startswith("Spire_Main"):
        obj.data.materials.append(roof)
    elif obj.name.startswith("Spire_Finial") or obj.name.startswith("cross"):
        obj.data.materials.append(metal)
    elif obj.name == "Ground":
        m = bpy.data.materials.new(name='GroundMat')
        m.use_nodes = True
        b = m.node_tree.nodes.get('Principled BSDF')
        b.inputs['Base Color'].default_value = (0.86,0.87,0.88,1)
        b.inputs['Roughness'].default_value = 0.95
        obj.data.materials.append(m)
    else:
        obj.data.materials.append(stone)

# Parent all spire parts (except ground) to empty
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
root = bpy.context.active_object
root.name = 'ChurchSpire'
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH' and obj.name != 'Ground':
        obj.parent = root

# Camera
bpy.ops.object.camera_add(location=(8.5, -8.5, 6.0), rotation=(math.radians(68), 0, math.radians(45)))
camera = bpy.context.active_object
scene.camera = camera

# Light
bpy.ops.object.light_add(type='SUN', location=(4,-4,10))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(40), math.radians(5), math.radians(35))

# Save blend
blend_path = os.path.join(OUT_DIR, 'church_spire_lowpoly.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# Export glb
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root
glb_path = os.path.join(OUT_DIR, 'church_spire_lowpoly.glb')
bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', use_selection=True)

# Render previews from different angles
angles = [35, 90, 145]
for i, a in enumerate(angles, start=1):
    r = 12.0
    z = 5.8
    rad = math.radians(a)
    camera.location.x = r * math.cos(rad)
    camera.location.y = r * math.sin(rad)
    camera.location.z = z
    direction = root.location - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT_DIR, f'preview_{i}.png')
    bpy.ops.render.render(write_still=True)

print('DONE', OUT_DIR)
