"""Cue workspace hash helpers for verifier reference alignment."""

def fnv1a64(seed: str) -> int:
    """Reference FNV-1a 64-bit digest used by disjunct default selection."""
    h = 1469598103934665603
    for ch in seed.encode("utf-8"):
        h ^= ch
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h
