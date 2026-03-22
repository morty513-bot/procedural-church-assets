import bpy, os, math
from mathutils import Vector

SRC='/home/azureuser/.openclaw/workspace/assets/church_spire_v6/church_spire_v6.blend'
OUT='/home/azureuser/.openclaw/workspace/assets/church_spire_v7'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.eevee.taa_render_samples=16

# VERY obvious sky: stylized sunset gradient
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

# bottom warm orange, middle pink, top deep blue
r = ramp.color_ramp
r.elements[0].position = 0.08
r.elements[0].color = (1.0, 0.55, 0.18, 1)
r.elements[1].position = 0.92
r.elements[1].color = (0.12, 0.20, 0.58, 1)
mid = r.elements.new(0.46)
mid.color = (0.92, 0.35, 0.62, 1)

mapn.inputs['Rotation'].default_value[0] = math.radians(90)
bg.inputs['Strength'].default_value = 1.25

links.new(texc.outputs['Generated'], mapn.inputs['Vector'])
links.new(mapn.outputs['Vector'], grad.inputs['Vector'])
links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bg.inputs['Color'])
links.new(bg.outputs['Background'], out.inputs['Surface'])

# Keep grass ground
for o in scene.objects:
    if o.type=='MESH' and o.name.lower()=='plane':
        if not o.data.materials:
            gm = bpy.data.materials.new('Ground')
            gm.use_nodes = True
            o.data.materials.append(gm)
        m = o.data.materials[0]
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (0.30, 0.52, 0.24, 1)
        bsdf.inputs['Roughness'].default_value = 0.95

# Lighting: slightly cooler key to contrast warm sky
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
if radius < 1: radius = 11

for i,ang in enumerate([35,90,145], start=1):
    rad = math.radians(ang)
    cam.location.x = center.x + radius*math.cos(rad)
    cam.location.y = center.y + radius*math.sin(rad)
    cam.location.z = center.z
    d = center - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'preview_v7_{i}.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v7.blend'))
print('DONE', OUT)
