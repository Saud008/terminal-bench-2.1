"""Behavioral verifier for riverbench job scheduler repair."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from reference_scheduler import (
    backoff_delay_ms,
    backoff_delay_ms_broken,
    build_procedural_jobs,
    claim_order,
    expected_backoff_after_fail,
    select_next,
)

APP = Path("/app")
CLI = "/usr/local/bin/riverbench"
CONFIG = APP / "config/scheduler.json"
CATALOG = APP / "fixtures/seed-catalog.json"
LISTEN = "127.0.0.1:8092"
BASE = f"http://{LISTEN}"
SEED = os.environ.get("VERIFIER_SEED", "riverbench-seed-7")
PATCHES = Path(__file__).resolve().parent / "patches"

PROTECTED_SHA256: dict[str, str | None] = {
    "fixtures/seed-catalog.json": None,
    "config/scheduler.json": None,
    "docs/scheduler-contract.md": None,
    "docs/worker-api.md": None,
    "docs/lease-contract.md": None,
}

_SERVER: subprocess.Popen[str] | None = None

# Verifier-only single-module fixes for partial-trap rebuilds (not agent guidance).
_PARTIAL_FIX_QUEUE = """package scheduler

import (
	"sort"

	"github.com/terminus/riverbench/internal/model"
)

func SelectNext(jobs []model.Job) (model.Job, bool) {
	if len(jobs) == 0 {
		return model.Job{}, false
	}
	sort.Slice(jobs, func(i, j int) bool {
		if jobs[i].Priority != jobs[j].Priority {
			return jobs[i].Priority < jobs[j].Priority
		}
		return jobs[i].ID < jobs[j].ID
	})
	return jobs[0], true
}
"""

_PARTIAL_FIX_BACKOFF = """package scheduler

func BackoffDelayMs(attempt int, baseMs int64, nowMs int64) int64 {
	_ = nowMs
	exp := attempt
	if exp < 0 {
		exp = 0
	}
	if exp > 30 {
		exp = 30
	}
	return baseMs * (1 << exp)
}
"""

_PARTIAL_FIX_HEARTBEAT = """package scheduler

import (
	"fmt"

	"github.com/terminus/riverbench/internal/model"
	"github.com/terminus/riverbench/internal/store"
)

func ExtendHeartbeat(st *store.Store, workerID, jobID string, nowMs, leaseMs int64) (model.Lease, error) {
	lease, err := st.GetLease(jobID)
	if err != nil {
		return model.Lease{}, fmt.Errorf("heartbeat: %w", err)
	}
	if lease.WorkerID != workerID {
		return model.Lease{}, fmt.Errorf("heartbeat: worker mismatch")
	}
	lease.ExpiresAtMs = nowMs + leaseMs
	lease.HeartbeatMs = nowMs
	if err := st.UpsertLease(lease); err != nil {
		return model.Lease{}, err
	}
	return lease, nil
}
"""

_PARTIAL_FIX_POISON = """package scheduler

import (
	"github.com/terminus/riverbench/internal/model"
)

func ApplyFailure(job model.Job, nowMs int64, baseMs int64, errMsg string) model.Job {
	job.Attempts++
	job.LastError = errMsg
	if job.Attempts >= job.MaxAttempts {
		job.State = model.StatePoison
		job.AvailableAt = 0
		return job
	}
	job.State = model.StatePending
	job.AvailableAt = nowMs + BackoffDelayMs(job.Attempts, baseMs, nowMs)
	return job
}
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


for rel in list(PROTECTED_SHA256):
    PROTECTED_SHA256[rel] = _sha256(APP / rel)


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:"
        + os.environ.get("PATH", ""),
    }
    proc = subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=env)
    if check and proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc


def reset_state() -> None:
    _run(["bash", str(APP / "scripts/reset-state.sh")])


def build_cli() -> None:
    _run(["bash", str(APP / "scripts/build-cli.sh")])


def stop_server() -> None:
    global _SERVER
    if _SERVER is None:
        return
    _SERVER.send_signal(signal.SIGTERM)
    try:
        _SERVER.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _SERVER.kill()
    _SERVER = None


def start_server() -> None:
    global _SERVER
    stop_server()
    env = {
        **os.environ,
        "PATH": "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:"
        + os.environ.get("PATH", ""),
    }
    _SERVER = subprocess.Popen(
        [CLI, "serve", "--listen", LISTEN, "--config", str(CONFIG), "--catalog", str(CATALOG)],
        cwd=str(APP),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
    )
    for _ in range(100):
        try:
            with urllib.request.urlopen(f"{BASE}/health", timeout=1.0) as resp:
                if resp.status == 200:
                    time.sleep(0.2)
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    raise RuntimeError("riverbench failed to start")


def _post(path: str, body: dict) -> dict | list:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _get(path: str) -> dict | list:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as resp:
        data = json.loads(resp.read().decode())
        return [] if data is None else data


def _apply_module_tree(
    backoff: str = "broken_backoff.go",
    queue: str = "broken_queue.go",
    heartbeat: str = "broken_heartbeat.go",
    poison: str = "broken_poison.go",
    store: str = "broken_store.go",
    *,
    inline: dict[str, str] | None = None,
) -> dict[str, str]:
    mapping = {
        "backoff": (APP / "internal/scheduler/backoff.go", backoff),
        "queue": (APP / "internal/scheduler/queue.go", queue),
        "heartbeat": (APP / "internal/scheduler/heartbeat.go", heartbeat),
        "poison": (APP / "internal/scheduler/poison.go", poison),
        "store": (APP / "internal/store/store.go", store),
    }
    backups = {str(dst): dst.read_text(encoding="utf-8") for dst, _ in mapping.values()}
    inline = inline or {}
    for key, (dst, filename) in mapping.items():
        if key in inline:
            dst.write_text(inline[key], encoding="utf-8")
        else:
            shutil.copy(PATCHES / filename, dst)
    build_cli()
    stop_server()
    start_server()
    return backups


def _restore_module_tree(backups: dict[str, str]) -> None:
    for dst, content in backups.items():
        Path(dst).write_text(content, encoding="utf-8")
    build_cli()
    stop_server()
    start_server()


def seed_jobs(seed: str = SEED) -> None:
    _post("/admin/seed", {"seed": seed})


@pytest.fixture(scope="module", autouse=True)
def _module_setup() -> None:
    """Build the CLI once and keep riverbench running for the module."""
    reset_state()
    build_cli()
    start_server()
    yield
    stop_server()


@pytest.fixture(autouse=True)
def _case_reset() -> None:
    """Reseed procedural jobs before each test case."""
    for _ in range(5):
        try:
            seed_jobs(SEED)
            return
        except (urllib.error.URLError, TimeoutError):
            stop_server()
            start_server()
    seed_jobs(SEED)


class TestIntegrity:
    def test_fixture_integrity(self) -> None:
        """Bundled contracts and catalog bytes must remain unchanged."""
        for rel, expected in PROTECTED_SHA256.items():
            assert _sha256(APP / rel) == expected

    def test_health(self) -> None:
        """HTTP health endpoint must respond before worker tests run."""
        with urllib.request.urlopen(f"{BASE}/health", timeout=5) as resp:
            assert resp.status == 200


class TestProceduralSeed:
    def test_seed_payloads_mutate_with_verifier_seed(self) -> None:
        """Procedural seed must derive payload and priority from VERIFIER_SEED."""
        jobs = _get("/admin/jobs")
        ref = build_procedural_jobs(SEED)
        by_id = {j["id"]: j for j in jobs}
        for r in ref:
            assert r["payload"] == by_id[r["id"]]["payload"]
            assert r["priority"] == by_id[r["id"]]["priority"]

    @pytest.mark.parametrize("alt_seed", ["river-alt-a", "river-alt-b"])
    def test_different_seed_changes_priority_and_payload(self, alt_seed: str) -> None:
        """Alternate seeds must change derived job metadata to block hardcoding."""
        seed_jobs(alt_seed)
        jobs = _get("/admin/jobs")
        ref = build_procedural_jobs(alt_seed)
        assert {j["payload"] for j in jobs} == {r["payload"] for r in ref}
        if alt_seed != SEED:
            assert {j["priority"] for j in jobs} != {
                r["priority"] for r in build_procedural_jobs(SEED)
            }


class TestPriorityQueue:
    def test_claim_order_matches_reference(self) -> None:
        """Claim order across the catalog must match the independent reference scheduler."""
        expected = claim_order(SEED)
        seen: list[str] = []
        for i in range(len(expected)):
            job = _post("/worker/claim", {"worker_id": f"w{i}"})
            seen.append(job["id"])
            _post(f"/worker/{job['id']}/ack", {"worker_id": f"w{i}"})
        assert seen == expected

    def test_priority_tie_break_lower_id_first(self) -> None:
        """Equal priorities must dequeue lexicographically smallest job id first."""
        seed_jobs(SEED)
        jobs = sorted(
            [j for j in _get("/admin/jobs") if j["priority"] == min(x["priority"] for x in _get("/admin/jobs"))],
            key=lambda j: j["id"],
        )
        first = _post("/worker/claim", {"worker_id": "tie-worker"})
        assert first["id"] == jobs[0]["id"]
        _post(f"/worker/{first['id']}/ack", {"worker_id": "tie-worker"})


class TestLeaseLifecycle:
    def test_ack_removes_lease_row(self) -> None:
        """Ack must delete the active lease row for that job."""
        job = _post("/worker/claim", {"worker_id": "lease-a"})
        leases_before = _get("/admin/leases")
        assert any(entry["job_id"] == job["id"] for entry in leases_before)
        _post(f"/worker/{job['id']}/ack", {"worker_id": "lease-a"})
        leases_after = _get("/admin/leases")
        assert all(entry["job_id"] != job["id"] for entry in leases_after)

    def test_finished_job_not_listed_in_leases(self) -> None:
        """Finished jobs must not remain visible in the lease table."""
        job = _post("/worker/claim", {"worker_id": "lease-b"})
        _post(f"/worker/{job['id']}/ack", {"worker_id": "lease-b"})
        jobs = _get("/admin/jobs?state=finished")
        assert any(j["id"] == job["id"] for j in jobs)
        leases = _get("/admin/leases")
        assert job["id"] not in {entry["job_id"] for entry in leases}


class TestBackoff:
    def test_fail_backoff_uses_attempt_exponent(self) -> None:
        """Failure backoff must follow attempt exponent, not wall-clock hour buckets."""
        seed_jobs(SEED)
        job = _post("/worker/claim", {"worker_id": "backoff-w"})
        now_ms = int(time.time() * 1000)
        _post(f"/worker/{job['id']}/fail", {"worker_id": "backoff-w", "error": "boom"})
        refreshed = next(j for j in _get("/admin/jobs") if j["id"] == job["id"])
        expected_at = expected_backoff_after_fail(0, now_ms)
        broken_at = now_ms + backoff_delay_ms_broken(1, 1000, now_ms)
        assert abs(refreshed["available_at_ms"] - expected_at) < 5000
        assert abs(refreshed["available_at_ms"] - broken_at) > 1000

    def test_multi_fail_backoff_ladder(self) -> None:
        """Repeated failures must increase retry delay according to attempt count."""
        body = {
            "seed": "backoff-ladder",
            "jobs": [
                {
                    "id": "ladder-01",
                    "kind": "retry",
                    "payload": "x",
                    "priority": 1,
                    "max_attempts": 8,
                }
            ],
        }
        _post("/admin/seed", body)
        delays: list[int] = []
        for attempt in range(3):
            job = _post("/worker/claim", {"worker_id": "bw"})
            t0 = int(time.time() * 1000)
            _post(f"/worker/{job['id']}/fail", {"worker_id": "bw", "error": "retry"})
            row = next(j for j in _get("/admin/jobs") if j["id"] == "ladder-01")
            delays.append(row["available_at_ms"] - t0)
            assert row["attempts"] == attempt + 1
            _post("/admin/force-ready", {"job_id": "ladder-01"})
        assert delays[0] < delays[1] < delays[2]
        assert delays[1] >= backoff_delay_ms(2) - 5000
        assert delays[2] >= backoff_delay_ms(3) - 5000


class TestPoison:
    def test_poison_after_max_attempts(self) -> None:
        """Jobs must enter poison state once attempts reach max_attempts."""
        body = {
            "seed": "poison-cap",
            "jobs": [
                {
                    "id": "poison-01",
                    "kind": "fragile",
                    "payload": "p",
                    "priority": 1,
                    "max_attempts": 2,
                }
            ],
        }
        _post("/admin/seed", body)
        for i in range(2):
            job = _post("/worker/claim", {"worker_id": "pw"})
            _post(f"/worker/{job['id']}/fail", {"worker_id": "pw", "error": "nope"})
            if i == 0:
                _post("/admin/force-ready", {"job_id": "poison-01"})
        row = next(j for j in _get("/admin/jobs") if j["id"] == "poison-01")
        assert row["state"] == "poison"
        assert row["attempts"] == 2
        with pytest.raises(urllib.error.HTTPError):
            _post("/worker/claim", {"worker_id": "pw2"})


class TestHeartbeat:
    def test_heartbeat_extends_requested_job_only(self) -> None:
        """Heartbeat on the wrong job id must not extend another worker's lease."""
        seed_jobs(SEED)
        alpha = _post("/worker/claim", {"worker_id": "ha"})
        beta = _post("/worker/claim", {"worker_id": "hb"})
        lease_beta_before = next(entry for entry in _get("/admin/leases") if entry["job_id"] == beta["id"])
        try:
            _post(f"/worker/{alpha['id']}/heartbeat", {"worker_id": "hb"})
        except urllib.error.HTTPError:
            pass
        lease_beta_after = next(entry for entry in _get("/admin/leases") if entry["job_id"] == beta["id"])
        assert lease_beta_after["expires_at_ms"] == lease_beta_before["expires_at_ms"]

    def test_heartbeat_extends_matching_lease(self) -> None:
        """Valid heartbeat must extend expiry for the leased job."""
        job = _post("/worker/claim", {"worker_id": "hc"})
        before = next(entry for entry in _get("/admin/leases") if entry["job_id"] == job["id"])
        time.sleep(0.05)
        after = _post(f"/worker/{job['id']}/heartbeat", {"worker_id": "hc"})
        assert after["expires_at_ms"] >= before["expires_at_ms"]


class TestAdminInject:
    def test_inject_stale_heartbeat_expiry(self) -> None:
        """Admin inject-heartbeat must set lease expiry for stuck-heartbeat scenarios."""
        job = _post("/worker/claim", {"worker_id": "inj"})
        stale = int(time.time() * 1000) - 60_000
        out = _post(
            "/admin/inject-heartbeat",
            {"job_id": job["id"], "worker_id": "inj", "expires_at_ms": stale},
        )
        assert out["expires_at_ms"] == stale
        lease = next(entry for entry in _get("/admin/leases") if entry["job_id"] == job["id"])
        assert lease["expires_at_ms"] == stale


class TestReferenceSim:
    def test_select_next_matches_reference_catalog(self) -> None:
        """First claim must match the reference dequeue pick for the seeded catalog."""
        jobs = build_procedural_jobs(SEED)
        for j in jobs:
            j["available_at_ms"] = 0
        pick = select_next(jobs)
        assert pick is not None
        first = _post("/worker/claim", {"worker_id": "ref"})
        assert first["id"] == pick["id"]


class TestFrontierTraps:
    def test_runtime_hour_bucket_backoff_still_wrong(self) -> None:
        """Hour-bucket backoff math must differ from contract attempt exponent at runtime."""
        seed_jobs(SEED)
        job = _post("/worker/claim", {"worker_id": "trap-hour"})
        now_ms = int(time.time() * 1000)
        _post(f"/worker/{job['id']}/fail", {"worker_id": "trap-hour", "error": "x"})
        row = next(j for j in _get("/admin/jobs") if j["id"] == job["id"])
        assert abs(row["available_at_ms"] - (now_ms + backoff_delay_ms(1))) < 5000

    def test_partial_fix_queue_only_lease_still_broken(self) -> None:
        """Fixing dequeue order alone must still leave stale leases after ack."""
        stop_server()
        start_server()
        backups = _apply_module_tree(inline={"queue": _PARTIAL_FIX_QUEUE})
        try:
            seed_jobs(SEED)
            first = _post("/worker/claim", {"worker_id": "partial-q"})
            _post(f"/worker/{first['id']}/ack", {"worker_id": "partial-q"})
            leases = _get("/admin/leases")
            assert any(entry["job_id"] == first["id"] for entry in leases)
        finally:
            _restore_module_tree(backups)

    def test_partial_fix_backoff_only_lease_still_broken(self) -> None:
        """Fixing backoff alone must still leave stale leases after ack."""
        backups = _apply_module_tree(inline={"backoff": _PARTIAL_FIX_BACKOFF})
        try:
            job = _post("/worker/claim", {"worker_id": "pb"})
            _post(f"/worker/{job['id']}/ack", {"worker_id": "pb"})
            leases = _get("/admin/leases")
            assert any(entry["job_id"] == job["id"] for entry in leases)
        finally:
            _restore_module_tree(backups)

    def test_partial_fix_heartbeat_only_poison_still_pending(self) -> None:
        """Fixing heartbeat alone must not enforce poison caps on repeated failures."""
        backups = _apply_module_tree(inline={"heartbeat": _PARTIAL_FIX_HEARTBEAT})
        try:
            body = {
                "seed": "partial-heartbeat",
                "jobs": [
                    {
                        "id": "hb-poison-01",
                        "kind": "fragile",
                        "payload": "p",
                        "priority": 1,
                        "max_attempts": 2,
                    }
                ],
            }
            _post("/admin/seed", body)
            for i in range(2):
                job = _post("/worker/claim", {"worker_id": "hbw"})
                _post(f"/worker/{job['id']}/fail", {"worker_id": "hbw", "error": "nope"})
                if i == 0:
                    _post("/admin/force-ready", {"job_id": "hb-poison-01"})
            row = next(j for j in _get("/admin/jobs") if j["id"] == "hb-poison-01")
            assert row["state"] == "pending"
        finally:
            _restore_module_tree(backups)

    def test_partial_fix_poison_only_queue_still_wrong(self) -> None:
        """Fixing poison handling alone must still dequeue jobs in the wrong order."""
        backups = _apply_module_tree(inline={"poison": _PARTIAL_FIX_POISON})
        try:
            seed_jobs(SEED)
            first = _post("/worker/claim", {"worker_id": "partial-p"})
            expected = claim_order(SEED)[0]
            assert first["id"] != expected
        finally:
            _restore_module_tree(backups)
