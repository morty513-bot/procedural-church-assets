import bpy
from mathutils import Vector

src='/home/azureuser/.openclaw/workspace/assets/church_spire_v18/church_spire_v18.blend'
bpy.ops.wm.open_mainfile(filepath=src)

print('OBJECTS:')
for o in bpy.context.scene.objects:
    if o.type!='MESH':
        continue
    pts=[o.matrix_world @ Vector(c) for c in o.bound_box]
    minz=min(p.z for p in pts); maxz=max(p.z for p in pts)
    minx=min(p.x for p in pts); maxx=max(p.x for p in pts)
    miny=min(p.y for p in pts); maxy=max(p.y for p in pts)
    print(f"{o.name:14s} loc=({o.location.x:.3f},{o.location.y:.3f},{o.location.z:.3f}) scale=({o.scale.x:.3f},{o.scale.y:.3f},{o.scale.z:.3f}) bounds x[{minx:.3f},{maxx:.3f}] y[{miny:.3f},{maxy:.3f}] z[{minz:.3f},{maxz:.3f}] mats={[m.name for m in o.data.materials]}")

print('\nMATERIALS:')
for m in bpy.data.materials:
    if m.use_nodes and m.node_tree:
        bsdf = next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'), None)
        if bsdf:
            c=bsdf.inputs['Base Color'].default_value
            r=bsdf.inputs['Roughness'].default_value
            print(f"{m.name}: color=({c[0]:.3f},{c[1]:.3f},{c[2]:.3f}), rough={r:.3f}")
    else:
        print(m.name)
