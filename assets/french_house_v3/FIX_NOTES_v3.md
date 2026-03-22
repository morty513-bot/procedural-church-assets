# French House v3 – Alignment Fix Notes

## What was fixed
- **Massing alignment:** Rebuilt the house massing so base + upper volumes are explicitly centered on the same XY origin (no accidental side-shift).
- **Roof seating and ridge coherence:** Replaced the previous roof primitive with a scripted **gable roof mesh** sized from upper-wall dimensions, with controlled embed and balanced overhang targets.
- **Chimney integration:** Repositioned chimney to penetrate the roof plane (embedded, not floating) and added a small flue element angled to read as roof-integrated.

## Script/refactor work
- Added `scripts/make_french_house_v3.py` with reusable geometric checks:
  - `assert_centered_xy`
  - `assert_roof_overhang_consistent`
  - `assert_roof_seating`
  - `assert_chimney_embedded`
- Added `scripts/render_french_house_v3_preview_checked.py` for consistent 3 wide previews + 1 detail view.

## Output
- `assets/french_house_v3/french_house_v3.blend`
- `assets/french_house_v3/french_house_v3.glb`
- `assets/french_house_v3/preview_checked_1.png`
- `assets/french_house_v3/preview_checked_2.png`
- `assets/french_house_v3/preview_checked_3.png`
- `assets/french_house_v3/preview_checked_detail.png`
