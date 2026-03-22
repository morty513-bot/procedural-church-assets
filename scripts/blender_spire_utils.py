"""Utility helpers for procedural church spire adjustments in Blender.

This module now includes lightweight *contract checks* so geometry placement
fails loudly when a contact relationship is broken.

Usage (from another script run via `blender -b -P ...`):

    from blender_spire_utils import (
        TopAssemblyConfig,
        open_scene,
        apply_top_assembly_policy,
        validate_top_assembly_contracts,
        compute_mesh_bounds,
        configure_camera_for_full_frame,
        render_angles,
        render_detail,
        export_selected_meshes,
    )
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import bpy
from mathutils import Vector


@dataclass(frozen=True)
class TopAssemblyConfig:
    """Declarative config for top-assembly placement relationships."""

    main_spire_name: str
    spike_names: tuple[str, ...]
    chain_names: tuple[str, ...]
    spike_base_offset: float = 0.015
    chain_overlap_epsilon: float = 0.015
    contact_tolerance: float = 1e-4


def open_scene(src_blend: str, width: int = 1280, height: int = 720, samples: int = 16):
    bpy.ops.wm.open_mainfile(filepath=src_blend)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.eevee.taa_render_samples = samples
    return scene


def by_name(name: str):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f'Missing object: {name}')
    return obj


def assert_objects_exist(names: Sequence[str], *, role: str = 'required') -> list:
    missing = [name for name in names if bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError(
            f'Missing {role} object(s): {missing}. '\
            'Check source .blend naming and config object lists.'
        )
    return [by_name(name) for name in names]


def assert_unique_names(names: Sequence[str], *, label: str = 'object list'):
    dups = sorted({name for name in names if names.count(name) > 1})
    if dups:
        raise RuntimeError(f'Duplicate names in {label}: {dups}')


def z_bounds(obj) -> tuple[float, float]:
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    zs = [p.z for p in pts]
    return min(zs), max(zs)


def set_min_z(obj, target_min_z: float):
    """Move object in world Z so its current min Z hits target_min_z.

    Uses `matrix_world.translation` instead of local `location.z` to avoid
    parent-scale induced drift.
    """
    current_min, _ = z_bounds(obj)
    delta = target_min_z - current_min
    world_t = obj.matrix_world.translation.copy()
    world_t.z += delta
    obj.matrix_world.translation = world_t


def set_group_min_z(objects: Iterable, target_min_z: float):
    for obj in objects:
        set_min_z(obj, target_min_z)


def set_chain_contacts(chain_objects: Sequence, epsilon: float = 0.015):
    """Lock contiguous contact along a vertical chain.

    For each pair (lower -> upper):
        upper.minZ = lower.maxZ - epsilon
    """
    for i in range(len(chain_objects) - 1):
        lower = chain_objects[i]
        upper = chain_objects[i + 1]
        _, lower_max = z_bounds(lower)
        target_upper_min = lower_max - epsilon
        set_min_z(upper, target_upper_min)


def chain_contact_errors(
    chain_objects: Sequence,
    *,
    epsilon: float,
    tolerance: float = 1e-4,
) -> list[str]:
    """Return descriptive contact errors for a lower->upper chain."""
    errors: list[str] = []
    for i in range(len(chain_objects) - 1):
        lower = chain_objects[i]
        upper = chain_objects[i + 1]
        _, lower_max = z_bounds(lower)
        upper_min, _ = z_bounds(upper)
        expected = lower_max - epsilon
        delta = upper_min - expected
        if abs(delta) > tolerance:
            errors.append(
                f'Contact mismatch {lower.name} -> {upper.name}: '
                f'upper.min={upper_min:.5f}, expected={expected:.5f}, '
                f'delta={delta:+.5f}, tol={tolerance:.5f}'
            )
    return errors


def assert_chain_contacts(
    chain_objects: Sequence,
    *,
    epsilon: float,
    tolerance: float = 1e-4,
):
    errors = chain_contact_errors(chain_objects, epsilon=epsilon, tolerance=tolerance)
    if errors:
        joined = '\n'.join(f'- {e}' for e in errors)
        raise RuntimeError(
            'Top-assembly chain contract failed. '\
            'Expected exact overlap policy not met:\n'
            f'{joined}'
        )


def assert_non_floating_chain(chain_objects: Sequence, *, max_gap: float = 0.0):
    """Ensure each upper piece is not floating above the previous piece."""
    errors: list[str] = []
    for i in range(len(chain_objects) - 1):
        lower = chain_objects[i]
        upper = chain_objects[i + 1]
        _, lower_max = z_bounds(lower)
        upper_min, _ = z_bounds(upper)
        gap = upper_min - lower_max
        if gap > max_gap:
            errors.append(
                f'Floating joint {lower.name} -> {upper.name}: '
                f'gap={gap:.5f}m (allowed <= {max_gap:.5f}m)'
            )
    if errors:
        raise RuntimeError('Floating joints detected:\n' + '\n'.join(f'- {e}' for e in errors))


def validate_top_assembly_contracts(config: TopAssemblyConfig):
    """Validate naming + placement contracts for top assembly."""
    assert_unique_names(config.spike_names, label='spike names')
    assert_unique_names(config.chain_names, label='chain names')

    if config.main_spire_name not in config.chain_names:
        raise RuntimeError(
            'Config mismatch: main_spire_name must be part of chain_names '\
            '(normally the first element).'
        )

    overlap = sorted(set(config.spike_names).intersection(config.chain_names))
    if overlap:
        raise RuntimeError(
            f'Config mismatch: spike names overlap chain names: {overlap}. '
            'Keep side spikes separate from central top chain.'
        )

    all_required = (config.main_spire_name,) + config.spike_names + config.chain_names
    assert_objects_exist(all_required, role='top assembly')

    main = by_name(config.main_spire_name)
    spikes = [by_name(n) for n in config.spike_names]
    chain = [by_name(n) for n in config.chain_names]

    main_min, _ = z_bounds(main)
    expected_spike_min = main_min + config.spike_base_offset

    spike_errors = []
    for s in spikes:
        s_min, _ = z_bounds(s)
        delta = s_min - expected_spike_min
        if abs(delta) > config.contact_tolerance:
            spike_errors.append(
                f'Spike base mismatch {s.name}: min={s_min:.5f}, '
                f'expected={expected_spike_min:.5f}, delta={delta:+.5f}, '
                f'tol={config.contact_tolerance:.5f}'
            )

    chain_errors = chain_contact_errors(
        chain,
        epsilon=config.chain_overlap_epsilon,
        tolerance=config.contact_tolerance,
    )

    if spike_errors or chain_errors:
        details = '\n'.join(f'- {msg}' for msg in (spike_errors + chain_errors))
        raise RuntimeError(
            'Top-assembly validation failed. Adjust config or placement order.\n'
            f'{details}'
        )

    assert_non_floating_chain(chain, max_gap=config.contact_tolerance)


def apply_top_assembly_policy(config: TopAssemblyConfig) -> Mapping[str, float]:
    """Apply declarative top-stack placement and immediately validate it."""
    assert_unique_names(config.spike_names, label='spike names')
    assert_unique_names(config.chain_names, label='chain names')

    main = by_name(config.main_spire_name)
    spikes = assert_objects_exist(config.spike_names, role='spike')
    chain = assert_objects_exist(config.chain_names, role='chain')

    main_min, _ = z_bounds(main)
    spike_target_min = main_min + config.spike_base_offset
    set_group_min_z(spikes, spike_target_min)
    set_chain_contacts(chain, epsilon=config.chain_overlap_epsilon)

    validate_top_assembly_contracts(config)

    return {
        'spike_target_min': spike_target_min,
        'chain_overlap_epsilon': config.chain_overlap_epsilon,
        'contact_tolerance': config.contact_tolerance,
    }


def compute_mesh_bounds(exclude_plane: bool = True):
    pts = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if exclude_plane and obj.name.lower() == 'plane':
            continue
        for c in obj.bound_box:
            pts.append(obj.matrix_world @ Vector(c))
    if not pts:
        raise RuntimeError('No mesh points found for bounds computation')
    min_v = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    max_v = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (min_v + max_v) * 0.5
    height = max_v.z - min_v.z
    return min_v, max_v, center, height


def configure_camera_for_full_frame(cam, center: Vector, height: float, margin: float = 1.35):
    fov = cam.data.angle_y
    half_h = (height * 0.5) * margin
    radius = (half_h / max(math.tan(fov * 0.5), 1e-4)) * 1.32
    look = center.copy()
    look.z = center.z + 0.05
    return radius, look


def render_angles(scene, cam, center: Vector, radius: float, look: Vector, out_dir: str, prefix: str, angles=(35, 90, 145), z_offset=0.7):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, angle in enumerate(angles, start=1):
        rad = math.radians(angle)
        cam.location.x = center.x + radius * math.cos(rad)
        cam.location.y = center.y + radius * math.sin(rad)
        cam.location.z = center.z + z_offset
        direction = look - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        path = os.path.join(out_dir, f'{prefix}_{i}.png')
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths


def render_detail(scene, cam, center: Vector, height: float, radius: float, out_path: str):
    cam.location = Vector((center.x + radius * 0.55, center.y - radius * 0.55, center.z + height * 0.25))
    look = center + Vector((0, 0, height * 0.25))
    direction = look - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    return out_path


def export_selected_meshes(glb_path: str, exclude_plane: bool = True):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if exclude_plane and obj.name.lower() == 'plane':
            continue
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', use_selection=True)
