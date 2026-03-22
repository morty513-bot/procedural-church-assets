# Church Spire v14 — Targeted Cube/Cylinder Contact Fix

Source: `assets/church_spire_v13/church_spire_v13.blend`

## Goal
Fix the specific floating joint where the cylinder atop the cube was separated, while leaving all other geometry unchanged.

## Identification (robust)
- Candidate cube objects: names starting with `Cube`
- Candidate cylinder objects: names starting with `Cylinder`
- Selected pair (name-first with sanity checks):
  - Cube: `Cube`
  - Cylinder: `Cylinder`
- Sanity checks:
  - XY center distance: `0.000000`
  - Z order check (`cylinder.maxZ > cube.maxZ`): `True`
  - Immediate-above by name + z sanity: `True`

## Contact enforcement
- Epsilon overlap target: **0.015 m**
- Enforced equation: **cylinder.minZ = cube.maxZ - epsilon**

## Measured before/after (world-space Z)

| Piece | Before minZ | Before maxZ | After minZ | After maxZ |
|---|---:|---:|---:|---:|
| Cube | 0.0000 | 6.4000 | 0.0000 | 6.4000 |
| Cylinder | 7.1500 | 9.3500 | 6.3850 | 8.5850 |

| Metric | Value |
|---|---:|
| Before gap (+) / overlap (-): cylinder.minZ - cube.maxZ | 0.7500 |
| Applied ΔZ to cylinder location.z | -0.7650 |
| After overlap (cube.maxZ - cylinder.minZ) | 0.0150 |
| Equation residual: cylinder.minZ - (cube.maxZ - epsilon) | 0.00000013 |

## Outputs
- `church_spire_v14.blend`
- `church_spire_v14.glb`
- `preview_v14_wide_1.png`
- `preview_v14_wide_2.png`
- `preview_v14_wide_3.png`
- `preview_v14_detail.png`
- `FIX_NOTES_v14.md`
