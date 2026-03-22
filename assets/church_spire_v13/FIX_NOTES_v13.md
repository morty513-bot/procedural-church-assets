# Church Spire v13 — Hard Contact Fix Notes

Source: `assets/church_spire_v12/church_spire_v12.blend`

## Goal
Enforce explicit geometric contact in the top ornament stack by measuring world-space Z bounds and forcing a small intentional overlap at every joint.

## Overlap policy
- Target overlap epsilon: **0.020 m** (upper min Z = lower max Z - epsilon).

## Measured joint contacts (world-space Z)

| Joint | Before lower max Z | Before upper min Z | Before gap (+) / overlap (-) | Applied ΔZ (upper) | After lower max Z | After upper min Z | After overlap |
|---|---:|---:|---:|---:|---:|---:|---:|
| Cone.001 -> Cylinder.001 | 15.4500 | 15.2800 | -0.1700 | +0.1500 | 15.4500 | 15.4300 | 0.0200 |
| Cylinder.001 -> Sphere | 15.7100 | 15.4800 | -0.2300 | +0.2100 | 15.7100 | 15.6900 | 0.0200 |
| Sphere -> Cube.005 | 15.9500 | 15.6975 | -0.2525 | +0.2325 | 15.9500 | 15.9300 | 0.0200 |
| Cube.005 -> Cube.006 | 16.1550 | 15.7965 | -0.3585 | +0.3385 | 16.1550 | 16.1350 | 0.0200 |

## Per-piece world Z bounds

| Piece | Before min Z | Before max Z | After min Z | After max Z |
|---|---:|---:|---:|---:|
| Cone.001 | 10.4500 | 15.4500 | 10.4500 | 15.4500 |
| Cylinder.001 | 15.2800 | 15.5600 | 15.4300 | 15.7100 |
| Sphere | 15.4800 | 15.7400 | 15.6900 | 15.9500 |
| Cube.005 | 15.6975 | 15.9225 | 15.9300 | 16.1550 |
| Cube.006 | 15.7965 | 15.8235 | 16.1350 | 16.1620 |

## Outputs

- `church_spire_v13.blend`
- `church_spire_v13.glb`
- `preview_v13_wide_1.png`
- `preview_v13_wide_2.png`
- `preview_v13_wide_3.png`
- `preview_v13_detail.png`
- `FIX_NOTES_v13.md`
