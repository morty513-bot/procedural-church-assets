# French House v1 (thatched, low-poly)

Stylized old French village house intended for broad readability at game-camera distance.

## Design choices
- **Massing:** stone lower block + lighter plaster upper block to suggest age and repairs over time.
- **Roof silhouette:** steep, simple 4-sided thatched roof with a ridge cap for a clear low-poly profile.
- **Regional cues:** narrow facade windows, simple timber corner accents, and masonry chimney.
- **Palette:** warm desaturated plaster/stone + straw roof to keep contrast readable in daylight.

## Script and tweak points
Generator: `scripts/make_french_house_v1.py`

Useful parameters near object creation:
- `base.scale` / `upper.scale` → overall footprint and wall height proportions.
- Roof primitive (`primitive_cone_add`):
  - `radius1` controls eave overhang.
  - `depth` controls roof steepness/height.
  - `rotation z=45°` keeps symmetric gable-like read in low-poly form.
- `assert_roof_over_walls(..., allowed_embed=...)` controls wall/roof join tolerance.
- Render angles in `render_views(..., angles=(...))` for alternate preview composition.

## Consistency checks included
- Base grounding check (main shell must sit at z=0).
- No mesh below ground check.
- Roof-to-wall embed/gap + silhouette check.

## Output files
- `french_house_v1.blend`
- `french_house_v1.glb`
- `preview_wide_1.png`
- `preview_wide_2.png`
- `preview_wide_3.png`
- `preview_detail.png`
