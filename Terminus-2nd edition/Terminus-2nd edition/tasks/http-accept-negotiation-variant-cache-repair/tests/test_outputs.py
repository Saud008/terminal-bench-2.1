"""Behavioral verifier for variantgate HTTP accept negotiation and cache contracts."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path

import pytest
from reference_variantgate import (
    build_procedural_catalog,
    header_dict,
    load_catalog,
    load_variants,
    negotiation_digest,
    prepare_headers,
    select_variant,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/variantgate")
CATALOG = APP / "fixtures/catalog.json"
SNAPSHOT = APP / "state/negotiation.snapshot.json"
BROKEN = Path("/opt/verifier-broken-gate")
module_oracles = Path(__file__).resolve().parent / "module_oracles"
VARY_HEADER = "Accept, Accept-Language, Accept-Charset"

MODULES = {
    "prepare": APP / "internal/negotiate/prepare.go",
    "rank": APP / "internal/negotiate/rank.go",
    "language": APP / "internal/negotiate/language.go",
    "select": APP / "internal/negotiate/select.go",
    "response": APP / "internal/cache/response.go",
    "snapshot": APP / "internal/staging/snapshot.go",
    "publish": APP / "internal/staging/publish.go",
    "guard": APP / "internal/staging/guard.go",
}

ORACLE_FILES = {
    "prepare": "ref_prepare.go",
    "rank": "ref_rank.go",
    "language": "ref_language.go",
    "select": "ref_select.go",
    "response": "ref_response.go",
    "snapshot": "ref_snapshot.go",
    "publish": "ref_publish.go",
    "guard": "ref_guard.go",
}
ORACLES = {name: module_oracles / fname for name, fname in ORACLE_FILES.items()}

EVAL_CASES = {
    "q-sort": {
        "resource": "q-sort",
        "headers": {"Accept": "application/json;q=0.8, text/plain;q=0.8"},
    },
    "charset": {
        "resource": "charset-case",
        "headers": {"Accept": "text/plain", "Accept-Charset": "iso-8859-1"},
    },
    "lang-en": {
        "resource": "lang-range",
        "headers": {"Accept": "application/json", "Accept-Language": "en;q=1.0,en-GB;q=0.4"},
    },
    "lang-gb": {
        "resource": "lang-range",
        "headers": {"Accept": "application/json", "Accept-Language": "en-GB;q=1.0,en;q=0.4"},
    },
    "no-match": {"resource": "no-match", "headers": {"Accept": "application/json"}},
    "wildcard": {
        "resource": "wildcard",
        "headers": {"Accept": "application/*;q=0.6,text/*;q=0.5"},
    },
    "lang-prefix": {
        "resource": "lang-prefix-trap",
        "headers": {
            "Accept": "application/json;q=0.9,application/xml;q=0.8",
            "Accept-Language": "en",
        },
    },
    "prepare-trap": {
        "resource": "prepare-trap",
        "headers": {"Accept": "application/json;q=0.9,text/plain;q=0.8"},
    },
    "accept-tie": {"resource": "accept-tie", "headers": {"Accept": "application/json"}},
    "charset-q": {
        "resource": "charset-q",
        "headers": {"Accept": "text/plain", "Accept-Charset": "utf-8;q=0.4, iso-8859-1;q=0.9"},
    },
}


def env() -> dict[str, str]:
    return {
        **os.environ,
        "PATH": "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:" + os.environ.get("PATH", ""),
    }


def reset_state() -> None:
    proc = subprocess.run(
        ["bash", str(APP / "scripts/reset-state.sh")],
        cwd=str(APP),
        capture_output=True,
        text=True,
        env=env(),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_variantgate() -> None:
    proc = subprocess.run(
        ["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/variantgate"],
        cwd=str(APP),
        capture_output=True,
        text=True,
        env=env(),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def snapshot_modules() -> dict[str, bytes]:
    return {name: path.read_bytes() for name, path in MODULES.items()}


def restore_modules(saved: dict[str, bytes]) -> None:
    for name, data in saved.items():
        MODULES[name].write_bytes(data)
        os.utime(MODULES[name], None)


def restore_broken_modules() -> None:
    for path in MODULES.values():
        src = BROKEN / path.name
        shutil.copyfile(src, path)
        os.utime(path, None)


def install_oracle_except(*broken_names: str) -> None:
    restore_broken_modules()
    skip = set(broken_names)
    for name, oracle_path in ORACLES.items():
        if name in skip:
            continue
        shutil.copyfile(oracle_path, MODULES[name])
        os.utime(MODULES[name], None)


def pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request(
    port: int,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, dict[str, str], bytes]:
    conn = HTTPConnection("127.0.0.1", port, timeout=3.0)
    conn.request(method, path, body=body, headers=headers or {})
    resp = conn.getresponse()
    data = resp.read()
    out_headers = {k.lower(): v for k, v in resp.getheaders()}
    status = resp.status
    conn.close()
    return status, out_headers, data


@contextmanager
def running_server(catalog_path: Path = CATALOG) -> int:
    port = pick_port()
    proc = subprocess.Popen(
        [
            str(CLI),
            "serve",
            "--listen",
            f"127.0.0.1:{port}",
            "--catalog",
            str(catalog_path),
        ],
        cwd=str(APP),
        env=env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        ready = False
        for _ in range(80):
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=1)
                raise AssertionError(f"variantgate exited early: {out}\n{err}")
            try:
                status, _, _ = request(port, "GET", "/health")
                if status == 200:
                    ready = True
                    break
            except OSError:
                pass
            time.sleep(0.05)
        assert ready, "server did not become healthy"
        yield port
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)


def case_path(case_key: str) -> str:
    return f"/resource/{EVAL_CASES[case_key]['resource']}"


def expected_for_case(catalog: dict, case_key: str) -> dict[str, object]:
    case = EVAL_CASES[case_key]
    resource = case["resource"]
    headers = dict(case["headers"])
    raw = header_dict(headers)
    prepared = prepare_headers(raw)
    variants = load_variants(catalog, resource)
    selected = select_variant(variants, raw)
    path = case_path(case_key)
    digest = negotiation_digest(path, resource, raw, prepared)
    if selected is None:
        return {"status": 406, "body": "", "content_type": "", "digest": digest}
    return {
        "status": 200,
        "body": selected.body,
        "content_type": f"{selected.media_type}; charset={selected.charset}",
        "digest": digest,
    }


def resource_request(port: int, case_key: str) -> tuple[int, dict[str, str], bytes]:
    case = EVAL_CASES[case_key]
    return request(port, "GET", case_path(case_key), headers=dict(case["headers"]))


def assert_case_matches_reference(
    port: int,
    case_key: str,
    catalog: dict,
    *,
    expected_cache: str = "MISS",
) -> tuple[int, dict[str, str], bytes]:
    status, headers, body = resource_request(port, case_key)
    expected = expected_for_case(catalog, case_key)
    assert status == expected["status"]
    assert headers.get("vary") == VARY_HEADER
    assert headers.get("x-cache") == expected_cache
    if expected["status"] == 200:
        assert body.decode("utf-8") == expected["body"]
        assert headers.get("content-type") == expected["content_type"]
    else:
        assert body.decode("utf-8") == ""
    return status, headers, body


def read_snapshot() -> dict:
    assert SNAPSHOT.is_file(), f"missing snapshot {SNAPSHOT}"
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset_and_restore_modules() -> None:
    saved = snapshot_modules()
    reset_state()
    yield
    restore_modules(saved)
    reset_state()


class TestVariantGate:
    def test_cli_binary_exists(self) -> None:
        """Verify cli binary exists."""
        assert CLI.is_file()

    def test_go_build_variantgate_binary(self) -> None:
        """Verify go build variantgate binary."""
        build_variantgate()
        assert CLI.is_file()

    def test_health_endpoint_ok(self) -> None:
        """Verify health endpoint ok."""
        with running_server() as port:
            status, headers, body = request(port, "GET", "/health")
            assert status == 200
            assert headers.get("content-type") == "application/json; charset=utf-8"
            assert body.decode("utf-8") == '{"status":"ok"}'

    def test_q_sort_matches_reference(self) -> None:
        """Verify q sort matches reference."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            assert_case_matches_reference(port, "q-sort", catalog)

    def test_charset_case_matches_reference(self) -> None:
        """Verify charset case matches reference."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            assert_case_matches_reference(port, "charset", catalog)

    def test_lang_en_matches_reference(self) -> None:
        """Verify lang en matches reference."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            assert_case_matches_reference(port, "lang-en", catalog)

    def test_lang_gb_matches_reference(self) -> None:
        """Verify lang gb matches reference."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            assert_case_matches_reference(port, "lang-gb", catalog)

    def test_no_match_returns_406(self) -> None:
        """Verify no match returns 406."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            status, _, _ = assert_case_matches_reference(port, "no-match", catalog)
            assert status == 406

    def test_wildcard_matches_reference(self) -> None:
        """Verify wildcard matches reference."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            assert_case_matches_reference(port, "wildcard", catalog)

    def test_lang_prefix_matches_reference(self) -> None:
        """Verify lang prefix matches reference."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            assert_case_matches_reference(port, "lang-prefix", catalog)

    def test_prepare_trap_snapshot_raw_prepared_contract(self) -> None:
        """Verify prepare trap snapshot raw prepared contract."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            assert_case_matches_reference(port, "prepare-trap", catalog)
            snap = read_snapshot()
            expected = expected_for_case(catalog, "prepare-trap")
            assert snap["raw"]["Accept-Charset"] == ""
            assert snap["prepared"]["Accept-Charset"] == ""
            assert snap["negotiation_digest"] == expected["digest"]

    def test_accept_tie_earliest_variant_selected(self) -> None:
        """Verify accept tie earliest variant selected."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            status, headers, body = assert_case_matches_reference(port, "accept-tie", catalog)
            assert status == 200
            assert headers.get("content-type") == "application/json; charset=utf-8"
            assert body.decode("utf-8") == '{"first":true}'

    def test_charset_q_prefers_latin1(self) -> None:
        """Verify charset q prefers latin1."""
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            status, headers, body = assert_case_matches_reference(port, "charset-q", catalog)
            assert status == 200
            assert headers.get("content-type") == "text/plain; charset=iso-8859-1"
            assert body.decode("utf-8") == "latin1-preferred"

    def test_cache_key_uses_raw_headers(self) -> None:
        """Verify cache key uses raw headers."""
        with running_server() as port:
            # same path, distinct raw Accept-Charset values must create distinct MISS entries
            status1, headers1, body1 = request(
                port,
                "GET",
                "/resource/charset-q",
                headers={"Accept": "text/plain", "Accept-Charset": "utf-8"},
            )
            status2, headers2, body2 = request(
                port,
                "GET",
                "/resource/charset-q",
                headers={"Accept": "text/plain", "Accept-Charset": "iso-8859-1"},
            )
            assert status1 == 200
            assert status2 == 200
            assert headers1.get("x-cache") == "MISS"
            assert headers2.get("x-cache") == "MISS"
            assert body1.decode("utf-8") != body2.decode("utf-8")
            stats_status, _, stats_body = request(port, "GET", "/cache/stats")
            assert stats_status == 200
            stats = json.loads(stats_body.decode("utf-8"))
            assert stats == {"hits": 0, "misses": 2}

    def test_admin_catalog_reload_resets_cache(self) -> None:
        """Verify admin catalog reload resets cache."""
        custom = build_procedural_catalog("variantgate-proc-seed")
        resource_id = custom["_resource"]
        accept_header = custom["_accept"]
        payload = json.dumps({"resources": custom["resources"]}).encode("utf-8")
        with running_server() as port:
            # prime cache counters
            first_status, _, _ = request(port, "GET", "/resource/q-sort", headers={"Accept": "text/plain"})
            assert first_status in (200, 406)
            status, _, body = request(
                port,
                "POST",
                "/admin/catalog",
                headers={"Content-Type": "application/json"},
                body=payload,
            )
            assert status == 200
            assert json.loads(body.decode("utf-8")) == {"status": "reloaded"}
            stats_status, _, stats_body = request(port, "GET", "/cache/stats")
            assert stats_status == 200
            assert json.loads(stats_body.decode("utf-8")) == {"hits": 0, "misses": 0}
            res_status, res_headers, res_body = request(
                port,
                "GET",
                f"/resource/{resource_id}",
                headers={"Accept": accept_header},
            )
            cat = custom
            raw = header_dict({"Accept": accept_header})
            selected = select_variant(load_variants(cat, resource_id), raw)
            assert selected is not None
            assert res_status == 200
            assert res_headers.get("x-cache") == "MISS"
            assert res_body.decode("utf-8") == selected.body

    def test_verify_endpoint_detects_tampered_digest(self) -> None:
        """Verify verify endpoint detects tampered digest."""
        with running_server() as port:
            status, _, _ = request(port, "GET", "/resource/q-sort", headers={"Accept": "text/plain"})
            assert status == 200
            snap = read_snapshot()
            snap["negotiation_digest"] = "f" * 64
            SNAPSHOT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
            verify_status, _, verify_body = request(port, "GET", "/admin/negotiation/verify")
            assert verify_status == 200
            assert json.loads(verify_body.decode("utf-8")) == {"aligned": False}
            # pre-request guard must fail before ingest/cache
            status2, headers2, _ = request(port, "GET", "/resource/q-sort", headers={"Accept": "text/plain"})
            assert status2 == 406
            assert headers2.get("x-cache") == "MISS"
            persisted = read_snapshot()
            assert persisted["negotiation_digest"] == "f" * 64

    def test_procedural_catalog_matches_reference(self) -> None:
        """Verify procedural catalog matches reference."""
        custom = build_procedural_catalog("proc-matrix-seed")
        payload = json.dumps({"resources": custom["resources"]}).encode("utf-8")
        resource_id = custom["_resource"]
        accept_header = custom["_accept"]
        with running_server() as port:
            status, _, _ = request(
                port,
                "POST",
                "/admin/catalog",
                headers={"Content-Type": "application/json"},
                body=payload,
            )
            assert status == 200
            out_status, out_headers, out_body = request(
                port,
                "GET",
                f"/resource/{resource_id}",
                headers={"Accept": accept_header},
            )
            raw = header_dict({"Accept": accept_header})
            selected = select_variant(load_variants(custom, resource_id), raw)
            assert selected is not None
            assert out_status == 200
            assert out_headers.get("content-type") == f"{selected.media_type}; charset={selected.charset}"
            assert out_body.decode("utf-8") == selected.body


class TestPartialFixTraps:
    def test_install_oracle_except_prepare_leaves_prepare_trap(self) -> None:
        """Verify install oracle except prepare leaves prepare trap."""
        install_oracle_except("prepare")
        build_variantgate()
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            status, headers, body = resource_request(port, "prepare-trap")
            expected = expected_for_case(catalog, "prepare-trap")
            mismatch = (
                status != expected["status"]
                or headers.get("content-type", "") != expected["content_type"]
                or body.decode("utf-8") != expected["body"]
            )
            assert mismatch

    def test_install_oracle_except_rank_leaves_accept_tie_trap(self) -> None:
        """Verify install oracle except rank leaves accept tie trap."""
        install_oracle_except("rank")
        build_variantgate()
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            status, headers, body = resource_request(port, "accept-tie")
            expected = expected_for_case(catalog, "accept-tie")
            mismatch = (
                status != expected["status"]
                or headers.get("content-type", "") != expected["content_type"]
                or body.decode("utf-8") != expected["body"]
            )
            assert mismatch

    def test_install_oracle_except_language_leaves_lang_prefix_trap(self) -> None:
        """Verify install oracle except language leaves lang prefix trap."""
        install_oracle_except("language")
        build_variantgate()
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            status, headers, body = resource_request(port, "lang-prefix")
            expected = expected_for_case(catalog, "lang-prefix")
            mismatch = (
                status != expected["status"]
                or headers.get("content-type", "") != expected["content_type"]
                or body.decode("utf-8") != expected["body"]
            )
            assert mismatch

    def test_install_oracle_except_response_leaves_cache_key_trap(self) -> None:
        """Verify install oracle except response leaves cache key trap."""
        install_oracle_except("response")
        build_variantgate()
        with running_server() as port:
            s1, h1, _ = request(
                port,
                "GET",
                "/resource/charset-q",
                headers={"Accept": "text/plain", "Accept-Charset": "utf-8"},
            )
            s2, h2, _ = request(
                port,
                "GET",
                "/resource/charset-q",
                headers={"Accept": "text/plain", "Accept-Charset": "iso-8859-1"},
            )
            assert s1 == 200 and s2 == 200
            # broken response cache collapses different raw headers to one key
            assert h1.get("x-cache") == "MISS"
            assert h2.get("x-cache") == "HIT"

    def test_install_oracle_except_guard_leaves_tamper_trap(self) -> None:
        """Verify install oracle except guard leaves tamper trap."""
        install_oracle_except("guard")
        build_variantgate()
        with running_server() as port:
            s1, _, _ = request(port, "GET", "/resource/q-sort", headers={"Accept": "text/plain"})
            assert s1 == 200
            snap = read_snapshot()
            snap["negotiation_digest"] = "0" * 64
            SNAPSHOT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
            verify_status, _, verify_body = request(port, "GET", "/admin/negotiation/verify")
            assert verify_status == 200
            # broken guard reports aligned true even after tamper
            assert json.loads(verify_body.decode("utf-8")) == {"aligned": True}


class TestGoldenOracle:
    def test_install_all_oracles_matches_eval_matrix(self) -> None:
        """Verify install all oracles matches eval matrix."""
        install_oracle_except()
        build_variantgate()
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            for case_key in EVAL_CASES:
                assert_case_matches_reference(port, case_key, catalog)

    def test_oracle_matrix_snapshot_digest_matches_reference(self) -> None:
        """Verify oracle matrix snapshot digest matches reference."""
        install_oracle_except()
        build_variantgate()
        catalog = load_catalog(CATALOG)
        with running_server() as port:
            for case_key in ("q-sort", "prepare-trap", "charset-q"):
                assert_case_matches_reference(port, case_key, catalog)
                snap = read_snapshot()
                expected = expected_for_case(catalog, case_key)
                assert snap["negotiation_digest"] == expected["digest"]

    def test_oracle_matrix_cache_and_verify_contracts(self) -> None:
        """Verify oracle matrix cache and verify contracts."""
        install_oracle_except()
        build_variantgate()
        with running_server() as port:
            s1, h1, _ = request(
                port,
                "GET",
                "/resource/charset-q",
                headers={"Accept": "text/plain", "Accept-Charset": "utf-8"},
            )
            s2, h2, _ = request(
                port,
                "GET",
                "/resource/charset-q",
                headers={"Accept": "text/plain", "Accept-Charset": "iso-8859-1"},
            )
            assert s1 == 200 and s2 == 200
            assert h1.get("x-cache") == "MISS"
            assert h2.get("x-cache") == "MISS"
            snap = read_snapshot()
            snap["negotiation_digest"] = "a" * 64
            SNAPSHOT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
            verify_status, _, verify_body = request(port, "GET", "/admin/negotiation/verify")
            assert verify_status == 200
            assert json.loads(verify_body.decode("utf-8")) == {"aligned": False}
