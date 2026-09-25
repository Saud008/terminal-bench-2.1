"""Seed policy helpers."""

from __future__ import annotations


def padding_px(catalog: dict, seed: int) -> int:
    return int(catalog["base_padding"])


def scale_factor(catalog: dict, seed: int) -> int:
    return max(1, int(seed % catalog["scale_mod"]))


def scaled_dim(base: int, scale: int) -> int:
    return max(1, base * scale)
