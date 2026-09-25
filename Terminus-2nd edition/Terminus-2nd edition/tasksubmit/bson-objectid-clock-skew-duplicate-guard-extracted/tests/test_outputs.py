"""WireId mint and intake batch verifier."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import signal
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest

from ref_srcursor import reference_document_delta, reference_expected_applied
from ref_objclock import expect_burst, extract_wireid_from_bson, machine_fingerprint, parse_hex

APP = Path("/app")
DB = Path("/app/data/oidguard.db")
CLI = "/usr/local/bin/wireclock"
BASE = "http://127.0.0.1:9090"
SEED = os.environ.get("VERIFIER_SEED", "wireclock-seed")
SNAPSHOT = Path("/app/state/digestseal-batch.json")
LEDGER = Path("/app/state/srcursor-by-path.json")
PATCHES = Path(__file__).resolve().parent / "patches"
TB3_PATCHES = Path(os.environ.get("TB3_FIXTURE_DIR", "/opt/verifier-fixtures/wireclock"))

_SERVER: subprocess.Popen[str] | None = None


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:" + os.environ.get("PATH", ""),
    }
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=env)


def _reset() -> None:
    proc = _run(["bash", str(APP / "tooling/reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def _build() -> None:
    proc = _run(["go", "build", "-mod=readonly", "-o", CLI, "./cmd/wireclock"])
    assert proc.returncode == 0, proc.stderr


def _stop() -> None:
    global _SERVER
    if _SERVER is None:
        return
    _SERVER.send_signal(signal.SIGTERM)
    try:
        _SERVER.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _SERVER.kill()
    _SERVER = None


def _start() -> None:
    global _SERVER
    _stop()
    env = {
        **os.environ,
        "PATH": "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:" + os.environ.get("PATH", ""),
    }
    _SERVER = subprocess.Popen(
        [CLI, "serve", "--listen", "127.0.0.1:9090", "--db", str(DB)],
        cwd=str(APP),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
    )
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{BASE}/health", timeout=0.5):
                return
        except (urllib.error.URLError, TimeoutError, Exception):
            time.sleep(0.1)
    raise RuntimeError("server failed to start")


def _mint(now_unix: int, machine_id: str, count: int, timeout: float = 5) -> list[str]:
    body = json.dumps({"now_unix": now_unix, "machine_id": machine_id, "count": count}).encode()
    req = urllib.request.Request(f"{BASE}/v1/mint", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return list(data["ids"])


def _machine(tag: str) -> str:
    return f"machine-{SEED}-{tag}"


def _admit(now_unix: int, machine: str, docs: list[dict]) -> dict:
    body = json.dumps({"documents": docs}).encode()
    req = urllib.request.Request(
        f"{BASE}/v1/admit",
        data=body,
        headers={
            "X-Test-Now": str(now_unix),
            "X-Machine-Id": machine,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def _payload(tag: str) -> dict:
    return {"tag": tag, "n": sum((SEED + tag).encode()) % 997}


def _batch_digest(machine_id: str, now_unix: int, docs: list[dict]) -> str:
    parts = [machine_id, str(now_unix)]
    for doc in docs:
        payload = json.dumps(doc["payload"], separators=(",", ":"))
        parts.append(f"{doc['client_seq']}|{payload}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _stats() -> dict:
    with urllib.request.urlopen(f"{BASE}/v1/stats", timeout=5) as resp:
        return json.loads(resp.read().decode())


def _resume(path: Path) -> dict:
    body = json.dumps({"resume_path": str(path)}).encode()
    req = urllib.request.Request(f"{BASE}/v1/resume", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def _write_resume(seed: str) -> Path:
    base = 1_700_600_000 + (sum(seed.encode()) % 2000)
    machine = f"resume-{seed}"
    lines = []
    for i in range(1, 5):
        lines.append(
            {
                "line": i,
                "now_unix": base + i,
                "machine_id": machine,
                "client_seq": 100 + i,
                "payload": {"seq": i, "salt": (sum((seed + str(i)).encode()) % 500)},
            }
        )
    fd, name = tempfile.mkstemp(suffix=".jsonl", dir="/app/work/jsonl-resume")
    os.close(fd)
    path = Path(name)
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return path


def _install_golden(modules: dict[str, Path]) -> None:
    for rel, src in modules.items():
        dest = APP / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


# Baseline Go files per package. Extra agent helper .go files are stashed during
# isolation overlays so they cannot clash with golden stubs, then restored.
_PKG_BASELINE_GO = {
    "pkg/objclock": {"types.go", "codec.go", "bsonwire.go", "generator.go"},
    "pkg/digestseal": {"snapshot.go"},
    "pkg/oidstore": {"commit.go"},
    "pkg/intakegate": {"service.go"},
    "pkg/srcursor": {"by_path.go"},
    "pkg/jsonlresume": {"apply.go"},
}


def _snapshot_tree(rels: list[str]) -> dict[str, str | None]:
    """Snapshot overlay targets plus any extra helper .go files in those packages."""
    saved: dict[str, str | None] = {}
    packages = {str(Path(rel).parent).replace("\\", "/") for rel in rels}
    for rel in rels:
        path = APP / rel
        saved[rel] = path.read_text(encoding="utf-8") if path.is_file() else None
    for pkg in packages:
        baseline = _PKG_BASELINE_GO.get(pkg, set())
        pkg_dir = APP / pkg
        if not pkg_dir.is_dir():
            continue
        for path in sorted(pkg_dir.glob("*.go")):
            rel = str(path.relative_to(APP)).replace("\\", "/")
            if path.name in baseline or rel in saved:
                continue
            saved[rel] = path.read_text(encoding="utf-8")
    return saved


def _restore_tree(saved: dict[str, str | None]) -> None:
    for rel, content in saved.items():
        dest = APP / rel
        if content is None:
            if dest.is_file():
                dest.unlink()
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


@contextmanager
def _isolation_overlay(modules: dict[str, Path]):
    """Apply golden stubs, hide agent helper .go files, then restore everything."""
    saved = _snapshot_tree(list(modules))
    packages = {str(Path(rel).parent).replace("\\", "/") for rel in modules}
    try:
        for pkg in packages:
            baseline = _PKG_BASELINE_GO.get(pkg, set())
            pkg_dir = APP / pkg
            if not pkg_dir.is_dir():
                continue
            for path in list(pkg_dir.glob("*.go")):
                if path.name not in baseline:
                    path.unlink()
        _install_golden(modules)
        yield
    finally:
        _restore_tree(saved)


class TestObjclockMint:
    def setup_method(self) -> None:
        _reset()
        _build()
        _start()

    def teardown_method(self) -> None:
        _stop()

    def test_t6d8396_mint_burst_counters(self) -> None:
        """Same-second mint bursts must allocate distinct per-second counters."""
        machine = _machine("burst")
        now = 1_700_000_000 + (sum(SEED.encode()) % 50_000)
        ids = _mint(now, machine, 6)
        assert len(ids) == len(set(ids))
        expected = expect_burst(now, machine, 6)
        for hex_id, exp in zip(ids, expected):
            ts, m, c = parse_hex(hex_id)
            assert ts == exp[0]
            assert m == exp[1]
            assert c == exp[2]

    def test_t6d8396_machine_bound_fingerprint(self) -> None:
        """Distinct machine ids must change the five-byte wire fingerprint."""
        now = 1_700_100_000
        a = _machine("a")
        b = _machine("b")
        id_a = _mint(now, a, 1)[0]
        id_b = _mint(now, b, 1)[0]
        _, ma, _ = parse_hex(id_a)
        _, mb, _ = parse_hex(id_b)
        assert ma == machine_fingerprint(a)
        assert mb == machine_fingerprint(b)
        assert ma != mb

    def test_t6d8396_mint_clock_skew_denied(self) -> None:
        """A backward mint clock after a later stamp must return HTTP 409."""
        machine = _machine("rollback")
        t1 = 1_700_200_100
        t0 = t1 - 120
        _mint(t1, machine, 1)
        body = json.dumps({"now_unix": t0, "machine_id": machine, "count": 1}).encode()
        req = urllib.request.Request(f"{BASE}/v1/mint", data=body, method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(req, timeout=5)
        assert exc.value.code == 409

    def test_t6d8396_mint_counter_exhaustion_denied(self) -> None:
        """Allocations past the 24-bit per-second counter must return HTTP 409."""
        machine = _machine("exhaust")
        now = 1_700_250_000
        batch = 65536
        target = 0xFFFFFF + 1
        generated = 0
        while generated < target:
            n = min(batch, target - generated)
            _mint(now, machine, n, timeout=120)
            generated += n
        body = json.dumps({"now_unix": now, "machine_id": machine, "count": 1}).encode()
        req = urllib.request.Request(f"{BASE}/v1/mint", data=body, method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(req, timeout=30)
        assert exc.value.code == 409

    def test_t6d8396_wire_document_attestation_round_trip(self) -> None:
        """Wire-doc responses must embed the minted ticket as BSON type 0x07."""
        machine = _machine("bson")
        now = 1_700_150_000
        hex_id = _mint(now, machine, 1)[0]
        payload = {"probe": SEED, "n": sum(SEED.encode()) % 97}
        body = json.dumps({"_id": hex_id, "payload": payload}).encode()
        req = urllib.request.Request(f"{BASE}/v1/wire-doc", data=body, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        raw = base64.b64decode(data["bson_b64"])
        extracted = extract_wireid_from_bson(raw)
        assert extracted == hex_id
        ts, m, c = parse_hex(extracted)
        assert ts == now
        assert m == machine_fingerprint(machine)
        assert c == 0

    def test_t6d8396_minted_ticket_hex_shape(self) -> None:
        """Minted tickets must be twenty-four lowercase hex characters."""
        machine = _machine("hexlen")
        hex_id = _mint(1_700_160_000, machine, 1)[0]
        assert len(hex_id) == 24
        assert hex_id == hex_id.lower()
        int(hex_id, 16)

    def test_t6d8396_mint_second_rotates_counter(self) -> None:
        """A new Unix second must reset the per-second counter to zero."""
        machine = _machine("reset")
        first = _mint(1_700_170_000, machine, 2)[-1]
        second = _mint(1_700_170_001, machine, 1)[0]
        _, _, c_first = parse_hex(first)
        _, _, c_second = parse_hex(second)
        assert c_second == 0
        assert c_first >= 1


class TestIntakeBatchHex:
    def setup_method(self) -> None:
        _reset()
        _build()
        _start()

    def teardown_method(self) -> None:
        _stop()

    def test_t6d8396_admit_vault_ticket_shape(self) -> None:
        """Successful admit must persist a contract-shaped wire id in the oidstore."""
        machine = _machine("persist")
        now = 1_700_300_000 + (sum(SEED.encode()) % 1000)
        res = _admit(now, machine, [{"client_seq": 1, "payload": _payload("one")}])
        assert res["results"][0]["repeat_claim"] is False
        hex_id = res["results"][0]["_id"]
        ts, m, c = parse_hex(hex_id)
        assert ts == now
        assert m == machine_fingerprint(machine)
        assert c == 0
        con = sqlite3.connect(DB)
        n = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        con.close()
        assert DB.is_file()
        assert n == 1

    def test_t6d8396_admit_clock_skew_denied(self) -> None:
        """Admit with an earlier X-Test-Now after a later stamp must return HTTP 409."""
        machine = _machine("clock")
        hi = 1_700_400_500
        lo = hi - 90
        _admit(hi, machine, [{"client_seq": 1, "payload": _payload("hi")}])
        body = json.dumps({"documents": [{"client_seq": 2, "payload": _payload("lo")}]}).encode()
        req = urllib.request.Request(
            f"{BASE}/v1/admit",
            data=body,
            headers={"X-Test-Now": str(lo), "X-Machine-Id": machine, "Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(req, timeout=5)
        assert exc.value.code == 409

    def test_t6d8396_admit_duplicate_ticket_preserves_vault(self) -> None:
        """Duplicate client_seq tickets must not overwrite sealed payload_json."""
        machine = _machine("dup")
        now = 1_700_500_000
        first_payload = _payload("original")
        second_payload = _payload("mutated")
        first = _admit(now, machine, [{"client_seq": 42, "payload": first_payload}])
        second = _admit(now + 1, machine, [{"client_seq": 42, "payload": second_payload}])
        assert second["results"][0]["repeat_claim"] is True
        assert second["results"][0]["_id"] == first["results"][0]["_id"]
        con = sqlite3.connect(DB)
        stored = con.execute(
            "SELECT payload_json FROM documents WHERE machine_id = ? AND client_seq = 42",
            (machine,),
        ).fetchone()[0]
        con.close()
        assert json.loads(stored) == first_payload

    def test_t6d8396_witness_seal_emitted_before_vault(self) -> None:
        """Admit must write a digest-bound witness before vault commit."""
        machine = _machine("snapshot")
        now = 1_700_300_111 + (sum(SEED.encode()) % 1000)
        docs = [{"client_seq": 1, "payload": _payload("snap")}]
        res = _admit(now, machine, docs)
        assert res["results"][0]["repeat_claim"] is False
        assert SNAPSHOT.is_file()
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["machine_id"] == machine
        assert snap["now_unix"] == now
        assert snap["batch_digest"] == _batch_digest(machine, now, docs)

    def test_t6d8396_witness_seal_lowercase_hex(self) -> None:
        """Witness batch_digest must be 64-character lowercase hex."""
        machine = _machine("digest-case")
        now = 1_700_302_000
        docs = [{"client_seq": 3, "payload": _payload("case")}]
        _admit(now, machine, docs)
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        digest = snap["batch_digest"]
        assert digest == digest.lower()
        assert len(digest) == 64

    def test_t6d8396_isolation_witness_without_vault_binding(self) -> None:
        """TB3 partial overlay: mint+digestseal without oidstore timestamp binding."""
        overlay = TB3_PATCHES if TB3_PATCHES.is_dir() else PATCHES
        with _isolation_overlay(
            {
                "pkg/objclock/generator.go": overlay / "objclock_mint.go",
                "pkg/digestseal/snapshot.go": overlay / "digestseal_batchhex.go",
                "pkg/oidstore/commit.go": overlay / "stub_oidstore.go",
                "pkg/intakegate/service.go": overlay / "stub_intakegate.go",
            }
        ):
            _build()
            _start()
            machine = _machine("partial")
            now = 1_700_301_000
            docs = [{"client_seq": 7, "payload": _payload("partial")}]
            res = _admit(now, machine, docs)
            assert res["results"][0]["repeat_claim"] is False
            ts, _, _ = parse_hex(res["results"][0]["_id"])
            assert ts != now
        _build()
        _start()


class TestJsonlResume:
    def setup_method(self) -> None:
        _reset()
        _build()
        _start()

    def teardown_method(self) -> None:
        _stop()

    def test_t6d8396_reapply_first_pass_vault_count(self) -> None:
        """First reapply of a journal must insert one vault row per line."""
        reapply = _write_resume(SEED)
        before = _stats()["documents"]
        out = _resume(reapply)
        after = _stats()["documents"]
        assert out["applied"] == reference_expected_applied(True, 4)
        assert after - before == reference_document_delta(True, 4)
        assert LEDGER.is_file()

    def test_t6d8396_reapply_duplicate_path_no_double_admit(self) -> None:
        """Replaying the same journal path again must not add vault rows."""
        reapply = _write_resume(SEED + "-twice")
        _resume(reapply)
        count_after_first = _stats()["documents"]
        out = _resume(reapply)
        count_after_second = _stats()["documents"]
        assert out["applied"] == reference_expected_applied(False, 4)
        assert count_after_second == count_after_first

    def test_t6d8396_reapply_restart_preserves_cursor(self) -> None:
        """After process restart, already-applied journal lines must stay skipped."""
        reapply = _write_resume(SEED + "-restart")
        _resume(reapply)
        first_docs = _stats()["documents"]
        _stop()
        _start()
        out = _resume(reapply)
        assert out["applied"] == reference_expected_applied(False, 4)
        assert _stats()["documents"] == first_docs

    def test_t6d8396_resume_path_scoped_cursor(self) -> None:
        """Applied lines on one journal path must not suppress another path."""
        reapply_a = _write_resume(SEED + "-path-a")
        reapply_b = _write_resume(SEED + "-path-b")
        assert _resume(reapply_a)["applied"] == 4
        assert _resume(reapply_b)["applied"] == 4
        assert _stats()["documents"] == 8
        assert LEDGER.is_file()

    def test_t6d8396_reapply_stats_reports_vault_records(self) -> None:
        """Stats must expose the vault document count after jsonlresume."""
        reapply = _write_resume(SEED + "-stats")
        before = _stats()["documents"]
        _resume(reapply)
        after = _stats()["documents"]
        assert after == before + 4

    def test_t6d8396_isolation_reapply_without_path_cursor(self) -> None:
        """TB3 overlay without path-scoped srcursor must cross-suppress line numbers."""
        overlay = TB3_PATCHES if TB3_PATCHES.is_dir() else PATCHES
        mapping = {
            "pkg/objclock/generator.go": overlay / "objclock_mint.go",
            "pkg/digestseal/snapshot.go": overlay / "digestseal_batchhex.go",
            "pkg/oidstore/commit.go": overlay / "oidstore_persist.go",
            "pkg/intakegate/service.go": overlay / "http_intake_handler.go",
            "pkg/jsonlresume/apply.go": overlay / "jsonlresume_apply.go",
            "pkg/srcursor/by_path.go": overlay / "stub_srcursor.go",
        }
        with _isolation_overlay(mapping):
            _build()
            _start()
            reapply_a = _write_resume(SEED + "-partial-a")
            reapply_b = _write_resume(SEED + "-partial-b")
            assert _resume(reapply_a)["applied"] == 4
            assert _resume(reapply_b)["applied"] == 0
        _build()
        _start()
