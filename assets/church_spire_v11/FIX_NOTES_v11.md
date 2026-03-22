# Church Spire v11 — Geometry Fix Notes

Source: `assets/church_spire_v10/church_spire_v10.blend`

## Fixes made

1. **Tip/finial stack connection fixed (no visible gap):**
   - Repositioned upper finial elements (`Cylinder.001`, `Sphere`, `Cube.005`, `Cube.006`) to ensure slight intentional overlap/contact between:
     - upper spire tip and collar,
     - collar and sphere,
     - sphere and cross.
   - Preserved original materials and silhouette style.

2. **Top spikes/pinnacles anchored and oriented:**
   - Updated `Cone.002`–`Cone.009` to:
     - tilt outward (~26°) from vertical for a more natural roof-edge crocketed/pinnacle feel,
     - move slightly inward/down so bases are embedded into the spire transition geometry (not floating).
   - Kept ring arrangement and Saint-Émilion-inspired ornamental language.

## Outputs

- `church_spire_v11.blend`
- `church_spire_v11.glb`
- `preview_v11_1.png`
- `preview_v11_2.png`
- `preview_v11_3.png`
- `preview_v11_detail.png`

