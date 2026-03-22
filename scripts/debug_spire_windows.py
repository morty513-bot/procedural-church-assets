import bpy, os
blend='/home/azureuser/.openclaw/workspace/assets/church_spire_v2/church_spire_v2.blend'
bpy.ops.wm.open_mainfile(filepath=blend)
for o in bpy.context.scene.objects:
    if o.type=='MESH' and o.name.startswith('Cube'):
        print(o.name, 'loc', tuple(round(v,3) for v in o.location), 'scale', tuple(round(v,3) for v in o.scale))
