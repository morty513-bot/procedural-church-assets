import os
import sys

sys.path.append('/home/mainuser/.openclaw/workspace/scripts')

from blender_spire_utils import (
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

SRC = '/home/mainuser/.openclaw/workspace/assets/church_spire_v16/church_spire_v16.blend'
OUT = '/home/mainuser/.openclaw/workspace/assets/church_spire_v17'
os.makedirs(OUT, exist_ok=True)

scene = open_scene(SRC, width=1280, height=720, samples=16)
cam = scene.camera

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

_, _, center, height = compute_mesh_bounds(exclude_plane=True)
radius, look = configure_camera_for_full_frame(cam, center, height, margin=1.35)

render_angles(
    scene,
    cam,
    center=center,
    radius=radius,
    look=look,
    out_dir=OUT,
    prefix='preview_v17_wide',
    angles=(35, 90, 145),
    z_offset=0.7,
)

render_detail(
    scene,
    cam,
    center=center,
    height=height,
    radius=radius,
    out_path=os.path.join(OUT, 'preview_v17_detail.png'),
)

import bpy

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'church_spire_v17.blend'))
export_selected_meshes(os.path.join(OUT, 'church_spire_v17.glb'), exclude_plane=True)

with open(os.path.join(OUT, 'FIX_NOTES_v17.md'), 'w') as f:
    f.write('# v17 targeted downshift fix\n')
    f.write('- Refactored to shared helper contracts in scripts/blender_spire_utils.py\n')
    f.write(f"- Spike ring target minZ: {policy['spike_target_min']:.4f}\n")
    f.write(f"- Top-chain overlap epsilon: {policy['chain_overlap_epsilon']:.4f}\n")
    f.write(f"- Contact tolerance: {policy['contact_tolerance']:.5f}\n")
    f.write('\n## Post-fix bounds\n')
    for n in (config.main_spire_name,) + config.spike_names + config.chain_names[1:]:
        o = by_name(n)
        mn, mx = z_bounds(o)
        f.write(f'- {n}: {mn:.4f} -> {mx:.4f}\n')

print('DONE', OUT)
