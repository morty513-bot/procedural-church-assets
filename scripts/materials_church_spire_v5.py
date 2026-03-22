import bpy, os, math
from mathutils import Vector

SRC='/home/azureuser/.openclaw/workspace/assets/church_spire_v2/church_spire_v2.blend'
OUT='/home/azureuser/.openclaw/workspace/assets/church_spire_v5'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.eevee.taa_render_samples=16

# Strong contrast materials
stone=bpy.data.materials.new('StoneV5'); stone.use_nodes=True
s=stone.node_tree.nodes['Principled BSDF']
s.inputs['Base Color'].default_value=(0.86,0.82,0.70,1)
s.inputs['Roughness'].default_value=0.92

roof=bpy.data.materials.new('RoofV5'); roof.use_nodes=True
r=roof.node_tree.nodes['Principled BSDF']
r.inputs['Base Color'].default_value=(0.05,0.07,0.16,1)
r.inputs['Roughness'].default_value=0.58

window=bpy.data.materials.new('WindowV5'); window.use_nodes=True
w=window.node_tree.nodes['Principled BSDF']
w.inputs['Base Color'].default_value=(0.07,0.75,0.98,1)
w.inputs['Emission Color'].default_value=(0.07,0.75,0.98,1)
w.inputs['Emission Strength'].default_value=1.8
w.inputs['Transmission Weight'].default_value=0.9
w.inputs['Roughness'].default_value=0.01

metal=bpy.data.materials.new('MetalV5'); metal.use_nodes=True
m=metal.node_tree.nodes['Principled BSDF']
m.inputs['Base Color'].default_value=(0.96,0.8,0.25,1)
m.inputs['Metallic'].default_value=0.98
m.inputs['Roughness'].default_value=0.2

# Find windows by exact dimension pattern from source
window_objs=[]
for o in scene.objects:
    if o.type!='MESH' or not o.name.startswith('Cube'):
        continue
    if abs(o.scale.y-0.02)<1e-4 and abs(o.scale.x-0.12)<1e-4 and abs(o.scale.z-0.34)<1e-4:
        window_objs.append(o)

# Make windows MUCH bigger and slightly inset outward for visibility
for o in window_objs:
    o.scale.x = 0.42  # was 0.12
    o.scale.z = 1.05  # was 0.34
    o.scale.y = 0.05  # was 0.02

# Reassign materials
for o in scene.objects:
    if o.type!='MESH':
        continue
    o.data.materials.clear()
    n=o.name.lower()
    if o in window_objs:
        o.data.materials.append(window)
    elif 'cone' in n:
        o.data.materials.append(roof)
    elif 'sphere' in n or (n.startswith('cube') and o.location.z>12 and o.scale.z>2.0):
        o.data.materials.append(metal)
    elif n=='plane':
        g=bpy.data.materials.new('GroundV5'); g.use_nodes=True
        gb=g.node_tree.nodes['Principled BSDF']
        gb.inputs['Base Color'].default_value=(0.9,0.92,0.94,1)
        gb.inputs['Roughness'].default_value=0.95
        o.data.materials.append(g)
    else:
        o.data.materials.append(stone)

# Keep camera framing similar but slightly closer for readability
cam=scene.camera
target=bpy.data.objects.get('ChurchSpireV2')
center=Vector((0,0,6.5))
if target: center=target.location.copy(); center.z=6.5
radius=((cam.location.x-center.x)**2+(cam.location.y-center.y)**2)**0.5
if radius<1: radius=12.5
radius*=0.9

for i,ang in enumerate([35,90,145],start=1):
    rad=math.radians(ang)
    cam.location.x=center.x+radius*math.cos(rad)
    cam.location.y=center.y+radius*math.sin(rad)
    cam.location.z=center.z
    d=center-cam.location
    cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=os.path.join(OUT,f'preview_v5_{i}.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'church_spire_v5.blend'))
print('DONE', len(window_objs), 'windows')
