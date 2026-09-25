"""Seed policy helpers (golden)."""

from __future__ import annotations


def gutter_px(catalog: dict, seed: int) -> int:
    return catalog["base_gutter"] + (seed % catalog["gutter_stride"])


def scale_factor(catalog: dict, seed: int) -> int:
    return 1 + (seed % catalog["scale_mod"])


def scaled_dim(base: int, scale: int) -> int:
    return max(1, base * scale)
