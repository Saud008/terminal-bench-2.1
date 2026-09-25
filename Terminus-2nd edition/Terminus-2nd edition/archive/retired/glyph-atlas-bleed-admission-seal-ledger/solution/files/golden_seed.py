"""Seed policy helpers (golden)."""

from __future__ import annotations


def padding_px(catalog: dict, seed: int) -> int:
    return catalog["base_padding"] + (seed % catalog["padding_stride"])


def scale_factor(catalog: dict, seed: int) -> int:
    return 1 + (seed % catalog["scale_mod"])


def scaled_dim(base: int, scale: int) -> int:
    return max(1, base * scale)
