"""v19 visual upgrade for Saint-Emilion-inspired low-poly church spire.

Builds on v18 robust placement/contract pipeline while improving silhouette,
regional stone character, and Gothic-inspired vertical accents.
"""

import os
import sys
import math

import bpy
from mathutils import Vector

sys.path.append('/home/azureuser/.openclaw/workspace/scripts')

from blender_spire_utils import (  # noqa: E402
    TopAssemblyConfig,
    open_scene,
    apply_top_assembly_policy,
    validate_top_assembly_contracts,
    by_name,
    z_bounds,
    compute_mesh_bounds,
    configure_camera_for_full_frame,
    render_angles,
    render_detail,
    export_selected_meshes,
)

SRC = '/home/azureuser/.openclaw/workspace/assets/church_spire_v18/church_spire_v18.blend'
OUT = '/home/azureuser/.openclaw/workspace/assets/church_spire_v19'
os.makedirs(OUT, exist_ok=True)

scene = open_scene(SRC, width=1365, height=768, samples=24)
cam = scene.camera

# ---- stylistic/material tuning -------------------------------------------------
# Saint-Emilion cue: warm limestone, but keep low-poly readability and contrast.
stone = bpy.data.materials.get('StoneV10')
if stone and stone.use_nodes:
    bsdf = next((n for n in stone.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.79, 0.73, 0.63, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.90

stone_dark = bpy.data.materials.get('StoneDarkV10')
if stone_dark and stone_dark.use_nodes:
    bsdf = next((n for n in stone_dark.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.60, 0.54, 0.46, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.92

roof = bpy.data.materials.get('SlateRoofV10')
if roof and roof.use_nodes:
    bsdf = next((n for n in roof.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.09, 0.11, 0.20, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.58

# ---- geometry upgrades ---------------------------------------------------------
# 1) Belfry cornice belt (adds hierarchy between drum and lower roof).
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1.66, depth=0.18, location=(0.0, 0.0, 8.66))
cornice = bpy.context.active_object
cornice.name = 'V19_CorniceBelt'
cornice.data.materials.append(by_name('Cylinder').data.materials[0])

# 2) Lantern base collar to support the tall spire visually.
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1.18, depth=0.15, location=(0.0, 0.0, 9.82))
collar = bpy.context.active_object
collar.name = 'V19_LanternCollar'
collar.data.materials.append(by_name('Cone').data.materials[0])

# 3) Four corner pinnacles near belfry level (Gothic vertical accents).
for i, ang_deg in enumerate((45, 135, 225, 315), start=1):
    ang = math.radians(ang_deg)
    x = 1.50 * math.cos(ang)
    y = 1.50 * math.sin(ang)
    bpy.ops.mesh.primitive_cone_add(
        vertices=6,
        radius1=0.12,
        radius2=0.03,
        depth=0.85,
        location=(x, y, 9.08),
    )
    p = bpy.context.active_object
    p.name = f'V19_CornerPinnacle_{i}'
    mat = bpy.data.materials.get('AccentTerracottaV10')
    if mat:
        p.data.materials.append(mat)

# 4) Four small dormer/lucarne hints on lower spire, cardinal directions.
for i, ang_deg in enumerate((0, 90, 180, 270), start=1):
    ang = math.radians(ang_deg)
    x = 1.02 * math.cos(ang)
    y = 1.02 * math.sin(ang)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, 9.34))
    d = bpy.context.active_object
    d.name = f'V19_Lucarne_{i}'
    d.scale = (0.17, 0.07, 0.20)
    # orient broad face outwards
    d.rotation_euler[2] = ang
    mat = bpy.data.materials.get('StoneDarkV10')
    if mat:
        d.data.materials.append(mat)

# 5) Make cross finial slightly more legible at distance.
cross_v = by_name('Cube.005')
cross_h = by_name('Cube.006')
cross_v.scale = (0.34, 0.34, 2.60)
cross_h.scale = (2.30, 0.34, 0.34)

# Ensure top ornaments and finial obey strict placement contracts.
config = TopAssemblyConfig(
    main_spire_name='Cone.001',
    spike_names=tuple(f'Cone.00{i}' for i in range(2, 10)),
    chain_names=('Cone.001', 'Cylinder.001', 'Sphere', 'Cube.005', 'Cube.006'),
    spike_base_offset=0.015,
    chain_overlap_epsilon=0.015,
    contact_tolerance=1e-4,
)
policy = apply_top_assembly_policy(config)
validate_top_assembly_contracts(config)

# ---- framing and previews ------------------------------------------------------
_, _, center, height = compute_mesh_bounds(exclude_plane=True)
radius, look = configure_camera_for_full_frame(cam, center, height, margin=1.32)

wide_paths = render_angles(
    scene,
    cam,
    center=center,
    radius=radius,
    look=look,
    out_dir=OUT,
    prefix='preview_v19_wide',
    angles=(30, 90, 150),
    z_offset=0.74,
)

detail_path = render_detail(
    scene,
    cam,
    center=center,
    height=height,
    radius=radius,
    out_path=os.path.join(OUT, 'preview_v19_detail.png'),
)

# ---- save/export ---------------------------------------------------------------
scene_path = os.path.join(OUT, 'church_spire_v19.blend')
scene_glb = os.path.join(OUT, 'church_spire_v19.glb')

bpy.ops.wm.save_as_mainfile(filepath=scene_path)
export_selected_meshes(scene_glb, exclude_plane=True)

# ---- notes --------------------------------------------------------------------
notes_path = os.path.join(OUT, 'NOTES_v19.md')
with open(notes_path, 'w') as f:
    f.write('# Church Spire v19 — Saint-Emilion-inspired visual upgrade\n\n')
    f.write('## Chosen upgrade set\n')
    f.write('- Warmed limestone palette (regional Saint-Emilion cue) while preserving stylized low-poly shading.\n')
    f.write('- Added belfry cornice belt and lantern collar for clearer mass hierarchy.\n')
    f.write('- Added 4 corner pinnacles at belfry level to strengthen Gothic vertical rhythm.\n')
    f.write('- Added 4 compact lucarne-like accents on the lower spire for silhouette richness.\n')
    f.write('- Increased finial cross thickness for readability at wide framing distances.\n\n')
    f.write('## Why these changes\n')
    f.write('- Saint-Emilion churches read as warm limestone volumes with clear vertical articulation.\n')
    f.write('- Low-poly assets benefit from big-shape hierarchy (belt/collar) more than micro-detail.\n')
    f.write('- Repeated 4-way ornaments preserve coherence and avoid noisy asymmetry.\n\n')
    f.write('## Contract validation\n')
    f.write('- `apply_top_assembly_policy` executed successfully.\n')
    f.write('- `validate_top_assembly_contracts` passed with no errors.\n')
    f.write(f"- Spike minZ target: {policy['spike_target_min']:.4f}\n")
    f.write(f"- Chain overlap epsilon: {policy['chain_overlap_epsilon']:.4f}\n")
    f.write(f"- Contact tolerance: {policy['contact_tolerance']:.5f}\n\n")
    f.write('## Top assembly bounds (post-upgrade)\n')
    for n in (config.main_spire_name,) + config.spike_names + config.chain_names[1:]:
        o = by_name(n)
        mn, mx = z_bounds(o)
        f.write(f'- {n}: {mn:.4f} -> {mx:.4f}\n')
    f.write('\n## Outputs\n')
    f.write(f'- Blend: `{scene_path}`\n')
    f.write(f'- GLB: `{scene_glb}`\n')
    for p in wide_paths:
        f.write(f'- Preview (wide): `{p}`\n')
    f.write(f'- Preview (detail): `{detail_path}`\n')

print('DONE', OUT)
