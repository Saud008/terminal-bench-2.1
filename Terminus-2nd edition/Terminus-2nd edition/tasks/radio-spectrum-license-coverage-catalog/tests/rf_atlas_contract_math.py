"""Independent spectrum catalog expected math."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_MATH = Path("/app/scripts/rf_grant_math.py")
_SPEC = importlib.util.spec_from_file_location("rf_grant_math", _MATH)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)
reference_atlas = _MOD.reference_atlas
scoped_atlas_seq_id = _MOD.scoped_atlas_seq_id


def expected_after_first_compile(seed: str, bundle: str, bundle_path: Path) -> dict:
    return reference_atlas(seed, bundle, bundle_path, 1)


def expected_atlas_seq_id(seed: str, bundle: str, gen: int) -> str:
    return scoped_atlas_seq_id(seed, bundle, gen)
