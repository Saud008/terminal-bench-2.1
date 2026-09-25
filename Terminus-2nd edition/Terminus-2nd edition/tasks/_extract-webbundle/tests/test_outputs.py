"""Verifier tests for rust-webbundle-integrity-section-verifier."""
from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path
from urllib.parse import unquote

APP = Path("/app")
ENV = APP / "environment"
BIN = ENV / "bin" / "wbleguard"
BUILD = ENV / "scripts" / "build_all.sh"
STATE = APP / "state" / "exchange_attestation.jsonl"
OUT = APP / "output" / "bundle_attestation_report.json"
DEFAULT_BUNDLES = ENV / "fixtures" / "bundles"
META = ENV / "fixtures" / "bundle_meta.json"
HIDDEN_ROOT = Path("/opt/verifier-fixtures/wble_hidden")


def bundle_dir() -> Path:
    tb3 = os.environ.get("TB3_BUNDLE_DIR")
    if tb3:
        return Path(tb3)
    return DEFAULT_BUNDLES


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def rebuild() -> None:
    run(["bash", str(BUILD)])


def pipeline(bundles: Path | None = None) -> None:
    bundles = bundles or bundle_dir()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        STATE.unlink()
    if OUT.exists():
        OUT.unlink()
    run([str(BIN), "catalog-bundles", "--bundles-dir", str(bundles), "--staging", str(STATE)])
    run([str(BIN), "emit-attestation", "--staging", str(STATE), "--meta", str(META), "--out", str(OUT)])


def load_report() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def canonical_url(raw: str) -> str:
    scheme, rest = raw.split("://", 1) if "://" in raw else ("http", raw)
    scheme = scheme.lower()
    if "/" in rest:
        host, path = rest.split("/", 1)
        path = "/" + path
    else:
        host, path = rest, "/"
    if host.endswith(":80") and scheme == "http":
        host = host[:-3]
    if host.endswith(":443") and scheme == "https":
        host = host[:-4]
    host = host.lower()
    path = decode_path(unquote(path, errors="strict").lower())
    if "?" in path:
        p, q = path.split("?", 1)
        path = p + "?" + "&".join(sorted(q.split("&")))
    return f"{scheme}://{host}{path}"


def decode_path(path: str) -> str:
    if "?" in path:
        p, q = path.split("?", 1)
        return decode_path(p) + "?" + q
    parts = path.split("/")
    out = []
    for i, seg in enumerate(parts):
        if i == 0 and seg == "":
            out.append("")
            continue
        if not seg:
            continue
        if "%2F" in seg or "%2f" in seg:
            out.append(seg)
        else:
            out.append(unquote(seg, errors="strict"))
    joined = "/".join(out)
    if not joined.startswith("/"):
        joined = "/" + joined if joined else "/"
    return joined if joined else "/"


def normalize_headers(headers: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return sorted([(k.lower(), v.strip()) for k, v in headers], key=lambda x: x[0])


def exchange_digest(url: str, status: int, headers: list[tuple[str, str]], body: bytes) -> bytes:
    cu = canonical_url(url)
    hdr_block = "\n".join(f"{k}:{v}" for k, v in normalize_headers(headers))
    preimage = f"{cu}\n{status}\n{hdr_block}\n".encode() + body
    return hashlib.sha256(preimage).digest()


def url_in_scope(url: str, scopes: list[str]) -> bool:
    canon = canonical_url(url)
    for scope in scopes:
        sc = canonical_url(scope)
        if sc.endswith("/"):
            if canon.startswith(sc):
                return True
        elif canon == sc:
            return True
        elif canon.startswith(sc) and len(canon) > len(sc) and canon[len(sc)] == "/":
            return True
    return False


def mime_allowed(ct: str, allowed: list[str]) -> bool:
    base = ct.split(";")[0].strip().lower()
    return base in [a.lower() for a in allowed]


def read_wble(path: Path) -> dict:
    raw = path.read_bytes()
    assert raw[:4] == b"WBLE"
    off = 6
    primary, off = read_str_at(raw, off)
    scope_count = struct.unpack_from("<H", raw, off)[0]
    off += 2
    scopes = []
    for _ in range(scope_count):
        s, off = read_str_at(raw, off)
        scopes.append(s)
    mime_count = struct.unpack_from("<H", raw, off)[0]
    off += 2
    mimes = []
    for _ in range(mime_count):
        m, off = read_str_at(raw, off)
        mimes.append(m)
    ex_count = struct.unpack_from("<I", raw, off)[0]
    off += 4
    exchanges = []
    for _ in range(ex_count):
        variant_id = struct.unpack_from("<I", raw, off)[0]
        off += 4
        url, off = read_str_at(raw, off)
        status = struct.unpack_from("<H", raw, off)[0]
        off += 2
        hdr_count = struct.unpack_from("<H", raw, off)[0]
        off += 2
        headers = []
        for _ in range(hdr_count):
            k, off = read_str_at(raw, off)
            v, off = read_str_at(raw, off)
            headers.append((k, v))
        body_len = struct.unpack_from("<I", raw, off)[0]
        off += 4
        body = raw[off : off + body_len]
        off += body_len
        exchanges.append({"variant_id": variant_id, "url": url, "status": status, "headers": headers, "body": body})
    hashes = []
    if off + 4 <= len(raw) and raw[off : off + 4] == b"IHSH":
        off += 4
        hcount = struct.unpack_from("<I", raw, off)[0]
        off += 4
        for _ in range(hcount):
            hashes.append(raw[off : off + 32])
            off += 32
    return {
        "bundle_id": path.stem,
        "primary": primary,
        "scopes": scopes,
        "mimes": mimes,
        "exchanges": exchanges,
        "hashes": hashes,
    }


def read_str_at(raw: bytes, off: int) -> tuple[str, int]:
    ln = struct.unpack_from("<H", raw, off)[0]
    off += 2
    s = raw[off : off + ln].decode()
    return s, off + ln


def resolve_dup(exchanges: list[dict]) -> list[dict]:
    best: dict[str, dict] = {}
    for ex in exchanges:
        key = canonical_url(ex["url"])
        cur = best.get(key)
        if cur is None or ex["variant_id"] > cur["variant_id"]:
            best[key] = ex
    return sorted(best.values(), key=lambda e: canonical_url(e["url"]))


def wble_ref_stage_rows(bundles_path: Path) -> list[dict]:
    rows = []
    for wble in sorted(bundles_path.glob("*.wble")):
        bundle = read_wble(wble)
        resolved = resolve_dup(bundle["exchanges"])
        for ex in resolved:
            idx = next(i for i, e in enumerate(bundle["exchanges"]) if e["variant_id"] == ex["variant_id"])
            digest = exchange_digest(ex["url"], ex["status"], ex["headers"], ex["body"])
            expected = bundle["hashes"][idx] if idx < len(bundle["hashes"]) else None
            hash_ok = expected is None or digest == expected
            ct = next((v for k, v in ex["headers"] if k.lower() == "content-type"), "")
            rows.append(
                {
                    "bundle_id": bundle["bundle_id"],
                    "variant_id": ex["variant_id"],
                    "canonical_url": canonical_url(ex["url"]),
                    "hash_ok": hash_ok,
                    "in_scope": url_in_scope(ex["url"], bundle["scopes"]),
                    "ctype_ok": mime_allowed(ct, bundle["mimes"]) if ct else False,
                }
            )
    rows.sort(key=lambda r: r["canonical_url"])
    return rows


def wble_ref_evidence_totals(staging_rows: list[dict]) -> dict:
    bundles: dict[str, dict] = {}
    hash_fail = scope_fail = ctype_fail = verified = 0
    for row in staging_rows:
        b = bundles.setdefault(row["bundle_id"], {"bundle_id": row["bundle_id"], "exchanges": [], "findings": []})
        b["exchanges"].append(
            {
                "canonical_url": row["canonical_url"],
                "hash_ok": row["hash_ok"],
                "in_scope": row["in_scope"],
                "ctype_ok": row["ctype_ok"],
            }
        )
        if row["hash_ok"] and row["in_scope"] and row["ctype_ok"]:
            verified += 1
        if not row["hash_ok"]:
            hash_fail += 1
        if not row["in_scope"]:
            scope_fail += 1
        if not row["ctype_ok"]:
            ctype_fail += 1
    bundle_list = sorted(bundles.values(), key=lambda x: x["bundle_id"])
    for b in bundle_list:
        b["exchanges"].sort(key=lambda e: e["canonical_url"])
    return {
        "bundles": bundle_list,
        "totals": {
            "exchange_count": len(staging_rows),
            "verified_count": verified,
            "finding_count": hash_fail + scope_fail + ctype_fail,
            "hash_failures": hash_fail,
            "scope_violations": scope_fail,
            "ctype_violations": ctype_fail,
        },
    }


def reference_wble_evidence_bundle(bundles_path: Path) -> dict:
    """Independent reference for anti-spam probe detection."""
    return wble_ref_evidence_totals(wble_ref_stage_rows(bundles_path))


def test_wble_rebuild_succeeds():
    """Verify rebuild succeeds for the wbleguard attestation pipeline."""
    rebuild()
    assert BIN.is_file()


def test_wble_pipeline_exit_zero():
    """Verify pipeline exit zero for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    assert OUT.is_file()


def test_wble_output_schema_top_level():
    """Verify output schema top level for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    data = load_report()
    assert "bundles" in data and "totals" in data


def test_wble_totals_exchange_count_matches_staging():
    """Verify totals exchange count matches staging for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    staging = [json.loads(ln) for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert load_report()["totals"]["exchange_count"] == len(staging)


def test_wble_bundles_sorted_by_id():
    """Verify bundles sorted by id for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    ids = [b["bundle_id"] for b in load_report()["bundles"]]
    assert ids == sorted(ids)


def test_wble_alpha_bundle_present():
    """Verify alpha bundle present for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    assert any(b["bundle_id"] == "alpha" for b in load_report()["bundles"])


def test_wble_bravo_bundle_present():
    """Verify bravo bundle present for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    assert any(b["bundle_id"] == "bravo" for b in load_report()["bundles"])


def test_wble_duplicate_resolves_highest_variant():
    """Verify duplicate resolves highest variant for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    alpha = next(b for b in load_report()["bundles"] if b["bundle_id"] == "alpha")
    assert len(alpha["exchanges"]) == 1
    staging = [json.loads(ln) for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    alpha_rows = [r for r in staging if r["bundle_id"] == "alpha"]
    assert alpha_rows[0]["variant_id"] == 3


def test_wble_canonical_url_lowercase_host():
    """Verify canonical url lowercase host for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    staging = [json.loads(ln) for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    alpha = next(r for r in staging if r["bundle_id"] == "alpha")
    assert alpha["canonical_url"] == "https://cdn.example/app/index"


def test_wble_charset_content_type_allowed():
    """Verify charset content type allowed for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    staging = [json.loads(ln) for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    alpha = next(r for r in staging if r["bundle_id"] == "alpha")
    assert alpha["ctype_ok"] is True


def test_wble_bravo_scope_boundary_violation():
    """Verify bravo scope boundary violation for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    staging = [json.loads(ln) for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    bravo_out = next(r for r in staging if r["bundle_id"] == "bravo" and "applet" in r["canonical_url"])
    assert bravo_out["in_scope"] is False


def test_wble_staging_sorted_by_canonical_url():
    """Verify staging sorted by canonical url for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    urls = [json.loads(ln)["canonical_url"] for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert urls == sorted(urls)


def test_wble_hash_ok_for_alpha_reference():
    """Verify hash ok for alpha reference for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    ref = wble_ref_stage_rows(bundle_dir())
    staging = [json.loads(ln) for ln in STATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for got, exp in zip(staging, ref):
        assert got["canonical_url"] == exp["canonical_url"]
        assert got["hash_ok"] == exp["hash_ok"]


def test_wble_verified_count_reference():
    """Verify verified count reference for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    ref = wble_ref_evidence_totals(wble_ref_stage_rows(bundle_dir()))
    assert load_report()["totals"]["verified_count"] == ref["totals"]["verified_count"]


def test_wble_scope_violations_count_reference():
    """Verify scope violations count reference for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    ref = wble_ref_evidence_totals(wble_ref_stage_rows(bundle_dir()))
    assert load_report()["totals"]["scope_violations"] == ref["totals"]["scope_violations"]


def test_wble_finding_count_includes_all_violations():
    """Verify finding count includes all violations for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    t = load_report()["totals"]
    assert t["finding_count"] == t["hash_failures"] + t["scope_violations"] + t["ctype_violations"]


def test_wble_exchanges_sorted_within_bundle():
    """Verify exchanges sorted within bundle for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    for bundle in load_report()["bundles"]:
        urls = [e["canonical_url"] for e in bundle["exchanges"]]
        assert urls == sorted(urls)


def test_wble_export_idempotent_bytes():
    """Verify export idempotent bytes for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    first = OUT.read_bytes()
    pipeline()
    second = OUT.read_bytes()
    assert first == second


def test_wble_cli_ingest_only_then_export():
    """Verify cli ingest only then export for the wbleguard attestation pipeline."""
    rebuild()
    bundles = bundle_dir()
    staging = APP / "state" / "alt_staging.jsonl"
    out = APP / "output" / "alt_report.json"
    run([str(BIN), "catalog-bundles", "--bundles-dir", str(bundles), "--staging", str(staging)])
    run([str(BIN), "emit-attestation", "--staging", str(staging), "--meta", str(META), "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["totals"]["exchange_count"] >= 2


def test_wble_hidden_bundle_dir_when_present():
    """Hidden trap via /opt/verifier-fixtures/wble_hidden/bundles — not bundled alpha/bravo."""
    hidden = Path("/opt/verifier-fixtures/wble_hidden/bundles")
    if not hidden.is_dir() or not list(hidden.glob("*.wble")):
        return
    rebuild()
    pipeline(hidden)
    ref = wble_ref_evidence_totals(wble_ref_stage_rows(hidden))
    got = load_report()
    assert got["totals"]["exchange_count"] == ref["totals"]["exchange_count"]
    assert got["totals"]["verified_count"] == ref["totals"]["verified_count"]


def test_wble_tb3_bundle_dir_env_override():
    """TB3_BUNDLE_DIR must redirect ingest away from bundled fixtures."""
    tb3 = os.environ.get("TB3_BUNDLE_DIR")
    if not tb3:
        return
    alt = Path(tb3)
    if not alt.is_dir():
        return
    rebuild()
    pipeline(alt)
    ref = wble_ref_evidence_totals(wble_ref_stage_rows(alt))
    assert load_report()["totals"] == ref["totals"]


def test_wble_decoy_audit_wrap_not_in_output():
    """Verify decoy audit wrap not in output for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    raw = OUT.read_text(encoding="utf-8")
    assert "wrap_audit_score" not in raw


def test_wble_subprocess_independent_paths():
    """Verify subprocess independent paths for the wbleguard attestation pipeline."""
    rebuild()
    bundles = bundle_dir()
    staging = APP / "state" / "iso_staging.jsonl"
    out = APP / "output" / "iso_report.json"
    run([str(BIN), "catalog-bundles", "--bundles-dir", str(bundles), "--staging", str(staging)])
    run([str(BIN), "emit-attestation", "--staging", str(staging), "--meta", str(META), "--out", str(out)])
    assert json.loads(out.read_text(encoding="utf-8"))["totals"]["exchange_count"] >= 2


def test_wble_full_report_matches_reference():
    """Verify full report matches reference for the wbleguard attestation pipeline."""
    rebuild()
    pipeline()
    ref = wble_ref_evidence_totals(wble_ref_stage_rows(bundle_dir()))
    got = load_report()
    assert got["totals"] == ref["totals"]
    assert len(got["bundles"]) == len(ref["bundles"])
