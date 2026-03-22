import bpy, os, math
from mathutils import Vector

SRC='/home/azureuser/.openclaw/workspace/assets/church_spire_v7/church_spire_v7.blend'
OUT='/home/azureuser/.openclaw/workspace/assets/church_spire_v8'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.eevee.taa_render_samples=16

# Stable world-space Z gradient sky (Unity-like horizon behavior)
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

# Z in [-1,1] -> [0,1]
map_range.inputs['From Min'].default_value = -1.0
map_range.inputs['From Max'].default_value = 1.0
map_range.inputs['To Min'].default_value = 0.0
map_range.inputs['To Max'].default_value = 1.0
map_range.clamp = True

# Bottom to top colors (stable with camera yaw)
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.78, 0.88, 0.98, 1)  # horizon light blue
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (0.26, 0.44, 0.78, 1)  # zenith deeper blue

bg.inputs['Strength'].default_value = 1.1

links.new(coord.outputs['Generated'], separate.inputs['Vector'])
links.new(separate.outputs['Z'], map_range.inputs['Value'])
links.new(map_range.outputs['Result'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bg.inputs['Color'])
links.new(bg.outputs['Background'], out.inputs['Surface'])

# Keep grass ground simple
for o in scene.objects:
    if o.type=='MESH' and o.name.lower()=='plane':
        if not o.data.materials:
            gm = bpy.data.materials.new('GroundGrassV8')
            gm.use_nodes = True
            o.data.materials.append(gm)
        m = o.data.materials[0]
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (0.30, 0.52, 0.24, 1)
        bsdf.inputs['Roughness'].default_value = 0.95

# Lighting cleanup and re-add (neutral)
for o in list(scene.objects):
    if o.type=='LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.light_add(type='SUN', location=(7,-8,14))
sun = bpy.context.active_object
sun.data.energy = 3.6
sun.rotation_euler = (math.radians(45), math.radians(8), math.radians(25))

bpy.ops.object.light_add(type='AREA', location=(-6,6,7))
fill = bpy.context.active_object
fill.data.energy = 220
fill.data.size = 8
fill.rotation_euler = (math.radians(80), 0, math.radians(-35))

cam = scene.camera
target = bpy.data.objects.get('ChurchSpireV2') or bpy.data.objects.get('ChurchSpire')
center = Vector((0,0,6.5))
if target:
    center = target.location.copy(); center.z = 6.5

radius = ((cam.location.x-center.x)**2 + (cam.location.y-center.y)**2)**0.5
if radius < 1:
    radius = 11

for i,ang in enumerate([35,90,145], start=1):
    rad = math.radians(ang)
    cam.location.x = center.x + radius*math.cos(rad)
    cam.location.y = center.y + radius*math.sin(rad)
    cam.location.z = center.z
    d = center - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'preview_v8_{i}.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v8.blend'))
print('DONE', OUT)
