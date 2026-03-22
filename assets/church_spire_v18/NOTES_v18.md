# v18 refactor notes
- Placement now uses declarative `TopAssemblyConfig` in scripts/blender_spire_utils.py
- Validation contracts run after placement and fail loudly on object/contact mismatches
- Spike minZ target: 9.8700
- Chain overlap epsilon: 0.0150
- Contact tolerance: 0.00010

## Top assembly bounds
- Cone.001: 9.8550 -> 14.8550
- Cone.002: 9.8700 -> 10.2817
- Cone.003: 9.8700 -> 10.3107
- Cone.004: 9.8700 -> 10.2817
- Cone.005: 9.8700 -> 10.3107
- Cone.006: 9.8700 -> 10.2817
- Cone.007: 9.8700 -> 10.3107
- Cone.008: 9.8700 -> 10.2817
- Cone.009: 9.8700 -> 10.3107
- Cylinder.001: 14.8400 -> 15.1200
- Sphere: 15.1050 -> 15.3650
- Cube.005: 15.3500 -> 15.5750
- Cube.006: 15.5600 -> 15.5870
