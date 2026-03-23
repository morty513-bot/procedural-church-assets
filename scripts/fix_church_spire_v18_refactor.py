"""v18 spire fix/refactor script.

Goal:
- Keep v17 look.
- Keep top stack placement logic explicit + maintainable.
- Validate object naming/contact contracts and fail loudly if broken.
- Render verification frames to confirm no visual regression.
"""

import os
import sys

# Allow importing helper module from this same directory
sys.path.append('/home/mainuser/.openclaw/workspace/scripts')

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

SRC = '/home/mainuser/.openclaw/workspace/assets/church_spire_v17/church_spire_v17.blend'
OUT = '/home/mainuser/.openclaw/workspace/assets/church_spire_v18'
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

# Apply + assert the placement contract.
policy = apply_top_assembly_policy(config)
# Extra explicit verification pass (safe no-op if already valid).
validate_top_assembly_contracts(config)

# Frame and render
_, _, center, height = compute_mesh_bounds(exclude_plane=True)
radius, look = configure_camera_for_full_frame(cam, center, height, margin=1.35)

render_angles(
    scene,
    cam,
    center=center,
    radius=radius,
    look=look,
    out_dir=OUT,
    prefix='preview_v18_wide',
    angles=(35, 90, 145),
    z_offset=0.7,
)

render_detail(
    scene,
    cam,
    center=center,
    height=height,
    radius=radius,
    out_path=os.path.join(OUT, 'preview_v18_detail.png'),
)

# Save + export
scene_path = os.path.join(OUT, 'church_spire_v18.blend')
scene_glb = os.path.join(OUT, 'church_spire_v18.glb')

import bpy  # local after scene opened

bpy.ops.wm.save_as_mainfile(filepath=scene_path)
export_selected_meshes(scene_glb, exclude_plane=True)

# Short operator note for future edits
with open(os.path.join(OUT, 'NOTES_v18.md'), 'w') as f:
    f.write('# v18 refactor notes\n')
    f.write('- Placement now uses declarative `TopAssemblyConfig` in scripts/blender_spire_utils.py\n')
    f.write('- Validation contracts run after placement and fail loudly on object/contact mismatches\n')
    f.write(f"- Spike minZ target: {policy['spike_target_min']:.4f}\n")
    f.write(f"- Chain overlap epsilon: {policy['chain_overlap_epsilon']:.4f}\n")
    f.write(f"- Contact tolerance: {policy['contact_tolerance']:.5f}\n")
    f.write('\n## Top assembly bounds\n')
    for n in (config.main_spire_name,) + config.spike_names + config.chain_names[1:]:
        o = by_name(n)
        mn, mx = z_bounds(o)
        f.write(f'- {n}: {mn:.4f} -> {mx:.4f}\n')

print('DONE', OUT)
