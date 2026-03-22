import bpy
from mathutils import Vector

SRC='/home/azureuser/.openclaw/workspace/assets/church_spire_v12/church_spire_v12.blend'
bpy.ops.wm.open_mainfile(filepath=SRC)

dg=bpy.context.evaluated_depsgraph_get()

def z_bounds(obj):
    oe=obj.evaluated_get(dg)
    if oe.type!='MESH':
        return None
    m=oe.to_mesh()
    try:
        zs=[(oe.matrix_world @ v.co).z for v in m.vertices]
        return min(zs), max(zs)
    finally:
        oe.to_mesh_clear()

rows=[]
for o in bpy.data.objects:
    zb=z_bounds(o)
    if zb:
        rows.append((zb[1],zb[0],o.name,o.location.z))
rows.sort(reverse=True)
for mx,mn,name,locz in rows[:20]:
    print(f"{name:20s} minZ={mn:.4f} maxZ={mx:.4f} locZ={locz:.4f}")
