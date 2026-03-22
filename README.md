# Procedural Church Assets

Public repo for procedural Blender-generated church spire assets and reusable helper scripts.

## Contents
- `scripts/` Blender Python (`bpy`) helpers, generators, fix passes, and contract checks
- `assets/` generated `.blend`, `.glb`, previews, and notes by version

## Quick usage

Run Blender scripts headlessly:

```bash
blender -b -P scripts/fix_church_spire_v18_refactor.py
```

Run a contract test:

```bash
blender -b -P scripts/test_spire_contracts_v19.py
```

## Notes
- This repository tracks iterative variants (`church_spire_v*`) for reproducible history.
- Scripts are designed to be reusable for future procedural assets.
