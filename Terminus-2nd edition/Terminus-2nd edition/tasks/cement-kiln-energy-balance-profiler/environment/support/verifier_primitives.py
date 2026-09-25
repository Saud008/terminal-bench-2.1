"""Shared reference helpers for local doc cross-checks."""

KCAL_TO_MJ = 0.004184

def normalize_celsius(raw: float, unit: str) -> float:
    if unit.upper().startswith("K"):
        return raw - 273.15
    return raw

def apply_cal(temp_norm_c: float, offset: float) -> float:
    return temp_norm_c - offset
