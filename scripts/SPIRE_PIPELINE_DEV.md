# Spire Pipeline: Robustness + Extensibility Notes

This pipeline now follows a **declarative placement + contract validation** pattern.

## Why this pattern

For procedural Blender assets, brittle failures usually come from:
- Name drift (`Cone.006` renamed in a .blend)
- Implicit geometry assumptions (top piece expected to touch previous piece)
- Silent positioning errors after edits

The helper module (`scripts/blender_spire_utils.py`) addresses this by separating:
1. **Policy**: `TopAssemblyConfig` (what should exist and how it should contact)
2. **Application**: `apply_top_assembly_policy(...)` (set transforms)
3. **Verification**: `validate_top_assembly_contracts(...)` (assert contracts)

## Implemented contract checks

- `assert_objects_exist(...)`
  - Fails immediately if expected objects are missing.
- `assert_unique_names(...)`
  - Fails if duplicate names were accidentally placed in config.
- `assert_chain_contacts(...)` / `chain_contact_errors(...)`
  - Checks each pair in lower->upper chain against expected overlap epsilon.
- `assert_non_floating_chain(...)`
  - Explicitly checks there are no positive gaps (floating joints).
- `validate_top_assembly_contracts(...)`
  - Runs all top-assembly checks together with clear error messages.

## How to extend safely

When adding new top ornament elements:

1. Add object names to `TopAssemblyConfig` (`chain_names` order matters).
2. Keep chain order strictly lower -> upper.
3. Use one overlap epsilon for the whole chain unless there is a strong reason.
4. Run `fix_church_spire_v18_refactor.py` in Blender headless.
5. If validation fails, inspect the reported pair and adjust either object geometry or chain order.

## Suggested "contract test" usage pattern

For each new spire variant script:
- Reuse `TopAssemblyConfig`
- Call `apply_top_assembly_policy(config)`
- Immediately call `validate_top_assembly_contracts(config)`
- Abort build on exception (do not save/export partial outputs)

## Research references used for this pass

- Blender Python API best-practice page (style + script-quality guidance):
  - https://docs.blender.org/api/current/info_best_practice.html
- Python dataclasses docs (declarative config object pattern):
  - https://docs.python.org/3/library/dataclasses.html

(Brave web search API was unavailable in this environment, so references were fetched directly.)
