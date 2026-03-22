import bpy, os, math
from mathutils import Vector

SRC='/home/azureuser/.openclaw/workspace/assets/church_spire_v5/church_spire_v5.blend'
OUT='/home/azureuser/.openclaw/workspace/assets/church_spire_v6'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.eevee.taa_render_samples=16

# Nicer sky gradient via world nodes
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
grad = nodes.new('ShaderNodeTexGradient')
mapn = nodes.new('ShaderNodeMapping')
texc = nodes.new('ShaderNodeTexCoord')
ramp = nodes.new('ShaderNodeValToRGB')

# Sky-like light blue gradient
ramp.color_ramp.elements[0].position = 0.15
ramp.color_ramp.elements[0].color = (0.72, 0.84, 0.98, 1)
ramp.color_ramp.elements[1].position = 0.95
ramp.color_ramp.elements[1].color = (0.96, 0.98, 1.0, 1)

mapn.inputs['Rotation'].default_value[0] = math.radians(90)
bg.inputs['Strength'].default_value = 1.1

links.new(texc.outputs['Generated'], mapn.inputs['Vector'])
links.new(mapn.outputs['Vector'], grad.inputs['Vector'])
links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bg.inputs['Color'])
links.new(bg.outputs['Background'], out.inputs['Surface'])

# Ground as simple grass color
for o in scene.objects:
    if o.type == 'MESH' and o.name.lower() == 'plane':
        o.data.materials.clear()
        g = bpy.data.materials.new('GroundGrassV6')
        g.use_nodes = True
        b = g.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (0.34, 0.55, 0.30, 1)
        b.inputs['Roughness'].default_value = 0.95
        o.data.materials.append(g)

# Add a soft fill sun + rim light to separate white stone
# Remove existing lights first
for o in list(scene.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.light_add(type='SUN', location=(6,-8,15))
key = bpy.context.active_object
key.data.energy = 3.8
key.rotation_euler = (math.radians(45), math.radians(8), math.radians(25))

bpy.ops.object.light_add(type='AREA', location=(-6,7,6))
fill = bpy.context.active_object
fill.data.energy = 250
fill.data.size = 8
fill.rotation_euler = (math.radians(80), 0, math.radians(-40))

# Camera angles unchanged
cam = scene.camera
target = bpy.data.objects.get('ChurchSpireV2') or bpy.data.objects.get('ChurchSpire')
center = Vector((0,0,6.5))
if target:
    center = target.location.copy(); center.z = 6.5

radius = ((cam.location.x-center.x)**2 + (cam.location.y-center.y)**2)**0.5
if radius < 1:
    radius = 11.0

for i, ang in enumerate([35,90,145], start=1):
    rad = math.radians(ang)
    cam.location.x = center.x + radius*math.cos(rad)
    cam.location.y = center.y + radius*math.sin(rad)
    cam.location.z = center.z
    d = center - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'preview_v6_{i}.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v6.blend'))
print('DONE', OUT)
