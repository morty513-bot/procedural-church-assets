"""Contract test for spire top assembly in v18 output.

Run:
    blender -b -P scripts/test_spire_contracts_v18.py
"""

import sys

sys.path.append('/home/azureuser/.openclaw/workspace/scripts')

from blender_spire_utils import (  # noqa: E402
    TopAssemblyConfig,
    open_scene,
    validate_top_assembly_contracts,
)

SRC = '/home/azureuser/.openclaw/workspace/assets/church_spire_v18/church_spire_v18.blend'

open_scene(SRC, width=640, height=360, samples=1)

config = TopAssemblyConfig(
    main_spire_name='Cone.001',
    spike_names=tuple(f'Cone.00{i}' for i in range(2, 10)),
    chain_names=('Cone.001', 'Cylinder.001', 'Sphere', 'Cube.005', 'Cube.006'),
    spike_base_offset=0.015,
    chain_overlap_epsilon=0.015,
    contact_tolerance=1e-4,
)

validate_top_assembly_contracts(config)
print('OK: v18 top-assembly contracts are valid')
