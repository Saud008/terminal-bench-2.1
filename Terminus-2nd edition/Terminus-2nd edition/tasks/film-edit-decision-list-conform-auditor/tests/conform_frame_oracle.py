"""Independent SMPTE timecode and conform oracle (correct policy flags)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

DROP_FRAME_LINEAR = False
ALIAS_BIDIRECTIONAL = True
MISSING_BEFORE_ALIAS = False
PULLDOWN_NUMERATOR = 23976
DIGEST_INCLUDES_FINDINGS = True
PUBLISH_REOPEN = False

SEVERITY_WEIGHTS = {
    "df_span_drift": "high",
    "alias_orphan": "critical",
    "handle_exceeds_reel": "high",
    "offline_media_note": "medium",
    "telecine_pull_drift": "medium",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_edl(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("TITLE:") or line.startswith("FCM:"):
            continue
        parts = re.split(r"\s+", line)
        if len(parts) < 8:
            continue
        rows.append(
            {
                "edit": parts[0],
                "reel": parts[1],
                "track": parts[2],
                "trans": parts[3],
                "rec_in": parts[4],
                "rec_out": parts[5],
                "src_in": parts[6],
                "src_out": parts[7],
            }
        )
    return rows


def tc_to_frames(tc: str, fps: int, drop_frame: bool) -> int:
    h, m, s, f = (int(x) for x in tc.split(":"))
    frames = (h * 3600 + m * 60 + s) * fps + f
    if drop_frame and fps == 30 and not DROP_FRAME_LINEAR:
        total_minutes = h * 60 + m
        frames -= 2 * (total_minutes - total_minutes // 10)
    return frames


def resolve_reel(reel: str, alias_file: Path) -> str:
    if not alias_file.is_file():
        return reel
    forward: dict[str, str] = {}
    reverse: dict[str, str] = {}
    for raw in alias_file.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        alias, vault_id = line.split("=", 1)
        forward[alias.strip()] = vault_id.strip()
        if ALIAS_BIDIRECTIONAL:
            reverse[vault_id.strip()] = alias.strip()
    if reel in forward:
        return forward[reel]
    if reel in reverse:
        return reverse[reel]
    return reel


def load_sources(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["reel"]: int(row["frame_count"]) for row in data.get("reels", [])}


def load_missing(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    out: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.add(line)
    return out


def is_missing(reel: str, missing: set[str], alias_file: Path) -> bool:
    check = reel
    if not MISSING_BEFORE_ALIAS:
        check = resolve_reel(reel, alias_file)
    return check in missing


def handle_frame_budget(src_in: str, src_out: str, fps: int, pulldown: str) -> int:
    in_f = tc_to_frames(src_in, fps, False)
    out_f = tc_to_frames(src_out, fps, False)
    budget = out_f - in_f
    if pulldown == "23976" and PULLDOWN_NUMERATOR == 23976:
        budget = (budget * 24000 + 11988) // 23976
    return budget


def bundle_fingerprint(manifest: Path) -> str:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    root = manifest.parent
    parts = [manifest.read_bytes()]
    for rel in sorted(data.get("fingerprint_files", [])):
        fp = root / rel
        if fp.is_file():
            parts.append(fp.read_bytes())
    return sha256_bytes(b"".join(parts))


def resolve_bundle_paths(manifest: Path) -> dict[str, Any]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    root = manifest.parent
    out: dict[str, Any] = {"bundle_id": data["bundle_id"]}
    for key in ("edl", "sources", "aliases", "missing", "tc_map"):
        val = Path(data[key])
        out[key] = val if val.is_absolute() else (root / val).resolve()
    tc = json.loads(out["tc_map"].read_text(encoding="utf-8"))
    out["fps"] = int(tc.get("fps", 30))
    out["drop_frame"] = bool(tc.get("drop_frame"))
    out["pulldown"] = str(tc.get("pulldown", "none"))
    out["fingerprint"] = bundle_fingerprint(manifest)
    return out


def compute_seal_digest(edits: list[dict[str, Any]], diagnostics: list[dict[str, Any]]) -> str:
    body: dict[str, Any] = {"edits": edits}
    if DIGEST_INCLUDES_FINDINGS:
        body["diagnostics"] = diagnostics
    return sha256_bytes(json.dumps(body, sort_keys=True).encode())


def oracle_stage_snapshot(manifest: Path, run_seq: int = 1) -> dict[str, Any]:
    meta = resolve_bundle_paths(manifest)
    edits: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    sources = load_sources(meta["sources"])
    missing = load_missing(meta["missing"])
    alias_file = meta["aliases"]

    for row in parse_edl(meta["edl"]):
        reel = row["reel"]
        resolved = resolve_reel(reel, alias_file)
        rec_in_f = tc_to_frames(row["rec_in"], meta["fps"], meta["drop_frame"])
        rec_out_f = tc_to_frames(row["rec_out"], meta["fps"], meta["drop_frame"])
        src_in_f = tc_to_frames(row["src_in"], meta["fps"], meta["drop_frame"])
        src_out_f = tc_to_frames(row["src_out"], meta["fps"], meta["drop_frame"])
        rec_span = rec_out_f - rec_in_f
        src_span = src_out_f - src_in_f
        budget = handle_frame_budget(row["src_in"], row["src_out"], meta["fps"], meta["pulldown"])
        edits.append(
            {
                "edit": row["edit"],
                "reel": reel,
                "resolved_reel": resolved,
                "rec_in": row["rec_in"],
                "rec_out": row["rec_out"],
                "src_in": row["src_in"],
                "src_out": row["src_out"],
                "rec_in_frames": rec_in_f,
                "rec_out_frames": rec_out_f,
                "src_in_frames": src_in_f,
                "src_out_frames": src_out_f,
                "rec_span_frames": rec_span,
                "src_span_frames": src_span,
                "handle_budget_frames": budget,
            }
        )

        lookup = resolved
        if rec_span != src_span:
            diagnostics.append(
                {
                    "category": "df_span_drift",
                    "edit": row["edit"],
                    "reel": reel,
                    "rec_span": rec_span,
                    "src_span": src_span,
                }
            )

        if lookup not in sources:
            if not is_missing(reel, missing, alias_file):
                diagnostics.append(
                    {
                        "category": "alias_orphan",
                        "edit": row["edit"],
                        "reel": reel,
                        "resolved_reel": resolved,
                    }
                )
        else:
            avail = sources[lookup]
            if src_out_f > avail:
                diagnostics.append(
                    {
                        "category": "handle_exceeds_reel",
                        "edit": row["edit"],
                        "reel": resolved,
                        "src_out_frames": src_out_f,
                        "available_frames": avail,
                    }
                )

        if is_missing(reel, missing, alias_file):
            diagnostics.append(
                {
                    "category": "offline_media_note",
                    "edit": row["edit"],
                    "reel": reel,
                    "resolved_reel": resolved,
                    "suppressed": True,
                }
            )

        if meta["pulldown"] == "23976" and budget != src_span:
            diagnostics.append(
                {
                    "category": "telecine_pull_drift",
                    "edit": row["edit"],
                    "reel": reel,
                    "handle_budget": budget,
                    "src_span": src_span,
                }
            )

    digest = compute_seal_digest(edits, diagnostics)
    return {
        "bundle_id": meta["bundle_id"],
        "bundle_fingerprint": meta["fingerprint"],
        "seal_digest": digest,
        "run_seq": run_seq,
        "tc_profile": {
            "fps": meta["fps"],
            "drop_frame": meta["drop_frame"],
            "pulldown": meta["pulldown"],
        },
        "edits": edits,
        "diagnostics": diagnostics,
    }


def oracle_publish_atlas(snapshot: dict[str, Any]) -> dict[str, Any]:
    diagnostics = list(snapshot["diagnostics"])
    if PUBLISH_REOPEN:
        diagnostics.append(
            {"category": "publish_reopen_trap", "detail": "bundle paths reopened during publish"}
        )
    return {
        "bundle_id": snapshot["bundle_id"],
        "seal_digest": snapshot["seal_digest"],
        "edit_count": len(snapshot["edits"]),
        "diagnostic_count": len(diagnostics),
        "diagnostics": diagnostics,
        "edits": snapshot["edits"],
    }
