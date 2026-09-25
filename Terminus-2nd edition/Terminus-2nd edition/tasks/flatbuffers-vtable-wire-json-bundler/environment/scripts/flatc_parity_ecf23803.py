"""Reference JSON via preinstalled flatc (verifier only — not agent oracle)."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = Path("/opt/verifier-schema/scene.fbs")


def _run_flatc_json(bin_path: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="fb-ref-") as tmp:
        work = Path(tmp)
        local_bin = work / "input.bin"
        local_bin.write_bytes(bin_path.read_bytes())
        proc = subprocess.run(
            [
                "flatc",
                "--json",
                "--strict-json",
                "--defaults-json",
                "--raw-binary",
                str(SCHEMA),
                "--",
                str(local_bin),
            ],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr or proc.stdout)
        out_json = work / "input.json"
        if not out_json.is_file():
            raise RuntimeError("flatc did not emit JSON")
        return json.loads(out_json.read_text(encoding="utf-8"))


def build_buffer_bytes(scene: dict[str, Any]) -> bytes:
    with tempfile.TemporaryDirectory(prefix="fb-build-") as tmp:
        work = Path(tmp)
        json_path = work / "scene.json"
        json_path.write_text(json.dumps(scene), encoding="utf-8")
        proc = subprocess.run(
            ["flatc", "-b", str(SCHEMA), str(json_path)],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr or proc.stdout)
        produced = work / "scene.bin"
        if not produced.is_file():
            raise RuntimeError("flatc did not emit binary")
        return produced.read_bytes()


def procedural_scene(seed: str) -> dict[str, Any]:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    revision = int.from_bytes(digest[0:4], "little") % 900 + 100
    entity_id = int.from_bytes(digest[4:8], "little") % 50_000 + 1
    parent_id = int.from_bytes(digest[8:12], "little") % 50_000 + 50_001
    tag_count = digest[12] % 3
    name = f"proc-{digest[13]:02x}-{digest[14]:02x}"

    tags = []
    for i in range(tag_count):
        key = f"k{i}-{digest[15 + i]:02x}"
        val = f"v{i}-{digest[20 + i]:02x}"
        tags.append({"key": key, "value": val})

    root: dict[str, Any] = {
        "id": entity_id,
        "name": name,
        "position": {
            "x": float(digest[24] % 17) + 0.25,
            "y": float(digest[25] % 13) + 0.5,
            "z": float(digest[26] % 11) + 0.75,
        },
        "metrics": {
            "distance_m": float(int.from_bytes(digest[28:30], "little") % 1000) / 10.0,
            "flag_count": int.from_bytes(digest[30:32], "little") % 20,
        },
        "parent": {
            "id": parent_id,
            "name": f"parent-{digest[31]:02x}",
            "position": {"x": 0.0, "y": 1.0, "z": 2.0},
        },
    }
    if tags:
        root["tags"] = tags

    return {"revision": revision, "root": root}


def procedural_deep_nest(seed: str) -> dict[str, Any]:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    depth = 3 + (digest[0] % 2)
    revision = int.from_bytes(digest[1:5], "little") % 500 + 50
    names = [f"nest-{digest[i]:02x}" for i in range(6, 6 + depth)]
    entity: dict[str, Any] | None = None
    for level in range(depth - 1, -1, -1):
        node: dict[str, Any] = {
            "id": 10_000 + level,
            "name": names[level],
            "position": {
                "x": float((digest[12 + level] % 9) + 1),
                "y": float((digest[18 + level] % 7) + 1),
                "z": float((digest[24 + level] % 5) + 1),
            },
        }
        if entity is not None:
            node["parent"] = entity
        entity = node
    assert entity is not None
    return {"revision": revision, "root": entity}


def procedural_many_tags(seed: str) -> dict[str, Any]:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    tag_count = 3 + (digest[0] % 4)
    revision = int.from_bytes(digest[4:8], "little") % 800 + 100
    entity_id = int.from_bytes(digest[8:12], "little") % 90_000 + 1
    tags = []
    for i in range(tag_count):
        tags.append(
            {
                "key": f"tag-{digest[13 + i]:02x}-{i}",
                "value": f"val-{digest[20 + i]:02x}",
            }
        )
    return {
        "revision": revision,
        "root": {
            "id": entity_id,
            "name": f"multi-{digest[30]:02x}",
            "position": {
                "x": float(digest[28] % 11) + 0.1,
                "y": float(digest[29] % 13) + 0.2,
                "z": float(digest[30] % 17) + 0.3,
            },
            "tags": tags,
        },
    }


def write_procedural_case(root: Path, seed: str) -> tuple[Path, dict[str, Any]]:
    scene = procedural_scene(seed)
    bin_path = root / "procedural-scene.bin"
    bin_path.write_bytes(build_buffer_bytes(scene))
    return bin_path, scene


def write_procedural_deep_nest(root: Path, seed: str) -> tuple[Path, dict[str, Any]]:
    scene = procedural_deep_nest(seed)
    bin_path = root / "procedural-deep.bin"
    bin_path.write_bytes(build_buffer_bytes(scene))
    return bin_path, scene


def write_procedural_many_tags(root: Path, seed: str) -> tuple[Path, dict[str, Any]]:
    scene = procedural_many_tags(seed)
    bin_path = root / "procedural-tags.bin"
    bin_path.write_bytes(build_buffer_bytes(scene))
    return bin_path, scene


def hidden_absent_tags_scene() -> dict[str, Any]:
    """Root and nested parent omit tags; verifier-only scenario."""
    return {
        "revision": 501,
        "root": {
            "id": 1,
            "name": "hidden-no-tags",
            "position": {"x": 1.25, "y": 2.5, "z": 3.75},
            "metrics": {"distance_m": 6.28, "flag_count": 2},
            "parent": {
                "id": 2,
                "name": "hidden-parent-no-tags",
                "position": {"x": 0.0, "y": 1.0, "z": 2.0},
            },
        },
    }


def hidden_tag_order_scene() -> dict[str, Any]:
    """Tag vector wire order differs from alphabetical key order."""
    return {
        "revision": 777,
        "root": {
            "id": 50,
            "name": "hidden-order-probe",
            "position": {"x": 0.25, "y": 0.5, "z": 0.75},
            "tags": [
                {"key": "zebra", "value": "z"},
                {"key": "alpha", "value": "a"},
                {"key": "middle", "value": "m"},
            ],
        },
    }


def hidden_deep_parent_chain_scene() -> dict[str, Any]:
    """Four-level parent chain with metrics on the leaf."""
    return {
        "revision": 909,
        "root": {
            "id": 10,
            "name": "hidden-leaf",
            "position": {"x": 1.0, "y": 2.0, "z": 3.0},
            "metrics": {"distance_m": 41.375, "flag_count": 3},
            "parent": {
                "id": 11,
                "name": "hidden-mid",
                "position": {"x": 4.0, "y": 5.0, "z": 6.0},
                "parent": {
                    "id": 12,
                    "name": "hidden-upper",
                    "position": {"x": 7.0, "y": 8.0, "z": 9.0},
                    "parent": {
                        "id": 13,
                        "name": "hidden-root",
                        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    },
                },
            },
        },
    }


def hidden_combo_trap_scene() -> dict[str, Any]:
    """Verifier-only combo: nested absent tags, padded parent name, wire tag order."""
    return {
        "revision": 1207,
        "root": {
            "id": 70,
            "name": "combo-trap-leaf",
            "position": {"x": 3.0, "y": 2.0, "z": 1.0},
            "tags": [
                {"key": "zulu", "value": "z"},
                {"key": "alpha", "value": "a"},
                {"key": "mango", "value": "m"},
            ],
            "metrics": {"distance_m": 18.5, "flag_count": 4},
            "parent": {
                "id": 71,
                "name": "combo-trap-parent-with-long-padding-name",
                "position": {"x": 11.0, "y": 12.0, "z": 13.0},
                "parent": {
                    "id": 72,
                    "name": "combo-trap-root",
                    "position": {"x": 0.5, "y": 1.5, "z": 2.5},
                    "tags": [
                        {"key": "kx42", "value": "second"},
                        {"key": "alpha", "value": "first"},
                    ],
                },
            },
        },
    }


def write_hidden_case(root: Path, scene: dict[str, Any], name: str) -> Path:
    bin_path = root / name
    bin_path.write_bytes(build_buffer_bytes(scene))
    return bin_path


def _canonical_f32(value: float) -> float:
    """Compare floats by IEEE754 float32 semantics (not JSON text)."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value):
            child = normalize(value[key])
            if child is None:
                continue
            out[key] = child
        return out
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, float):
        return _canonical_f32(value)
    return value


def assert_scene_equal(got: dict[str, Any], expected: dict[str, Any]) -> None:
    assert normalize(got) == normalize(expected)
