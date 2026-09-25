"""Behavioral verifier for guild bank treasury ops ledger."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from reference_bank import (
    initial_gold_for_seed,
    interest_amount,
    interest_bps_for_seed,
    mutate_id,
    scenario_bound_transfer,
    scenario_concurrent_gold,
    scenario_interest_replay,
    scenario_stack_split,
    stack_qty_for_seed,
)

APP = Path("/app")
CONFIG = APP / "config" / "guildbank.json"
REPORT = APP / "output" / "guild-audit.json"
DB = APP / "work" / "guildbank.db"
CLI = Path("/usr/local/bin/guildbankd")
SEED = os.environ.get("VERIFIER_SEED", "guild-bank-seed-11")
EXTRA_SEEDS = ("guild-matrix-3", "guild-matrix-17", "guild-matrix-41")

# Digests for paths instruction.md marks off-limits (docs, config, fixtures).
PROTECTED_SHA256: dict[str, str] = {
    "config/guildbank.json": "d511e7d23612776ff492898d4771da373ab9d24acd2b90203d03ab7f2ac6d962",
    "docs/bank-contract.md": "ad7da8d9e805126b77d5b2f31f8d12756484c783149683c41f7693dcf6c01ca0",
    "docs/stack-split.md": "4cb45129ec1231623e589bf17e135f8986d14ba32431c75da36790e14cc83185",
    "docs/concurrency.md": "fe38ab8cacbc3edcf472ab34e4e0083b6cbb4153e1af4db7bb1422bf0ff3cbff",
    "docs/audit-order.md": "13ce81e3214e48e3ff345172b82cee51e0847a3e08e60816e101ecdf90f74174",
    "docs/bound-items.md": "55e05eea112a04177fcfab826ef12ced7afb5e6ae128d6185d879ff00b21a60c",
    "docs/interest-journal.md": "2d8b53b72541f5dd6e98797a6afa5ff4de1ed89e6c65b5bd8f2f46927f9cc8fe",
    "docs/export-schema.md": "301d487435bf35a524615a19c1c97a43c9ec4835e38f981ddcfa750bdf18cc7c",
    "docs/fixture-catalog.md": "752cc6c178f979bb297ca8dc4ec4824ee24472e24fe6d6d5820abcdcbe3da60b",
    "fixtures/catalog.json": "f349b8463abbee95603bf3a0847663902484384a6253472018172a1b43638bf8",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _stop_daemon() -> None:
    subprocess.run(["pkill", "-x", "guildbankd"], check=False)
    time.sleep(0.3)


def _start_daemon() -> None:
    _stop_daemon()
    subprocess.Popen(
        [str(CLI), "serve", "--config", str(CONFIG)],
        cwd=APP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=0.5)
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("guildbankd did not start")


def _request(
    method: str,
    path: str,
    body: dict | None = None,
    *,
    mono_ms: int | None = None,
) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if mono_ms is not None:
        headers["X-Test-Mono-Ms"] = str(mono_ms)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:8080{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if not raw:
            return exc.code, {}
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def _reset() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def _bootstrap(guild_id: str, gold: int, bps: int | None = None, mono_ms: int = 0) -> dict:
    body: dict = {"guild_id": guild_id, "initial_gold": gold}
    if bps is not None:
        body["interest_rate_bps"] = bps
    status, resp = _request("POST", "/v1/guild/bootstrap", body, mono_ms=mono_ms)
    assert status == 200, resp
    return resp


def _deposit_stack(
    guild_id: str,
    template: str,
    qty: int,
    *,
    bound: bool = False,
    mono_ms: int = 0,
) -> dict:
    body = {"item_template_id": template, "quantity": qty, "bound": bound}
    status, resp = _request(
        "POST",
        f"/v1/guild/{guild_id}/deposit/stack",
        body,
        mono_ms=mono_ms,
    )
    assert status == 200, resp
    return resp


def _withdraw_stack(
    guild_id: str,
    player_id: str,
    stack_id: str,
    qty: int,
    mono_ms: int = 0,
) -> tuple[int, dict]:
    return _request(
        "POST",
        f"/v1/guild/{guild_id}/withdraw/stack",
        {"player_id": player_id, "stack_id": stack_id, "quantity": qty},
        mono_ms=mono_ms,
    )


def _withdraw_gold(
    guild_id: str,
    player_id: str,
    amount: int,
    mono_ms: int = 0,
) -> tuple[int, dict]:
    return _request(
        "POST",
        f"/v1/guild/{guild_id}/withdraw/gold",
        {"player_id": player_id, "amount": amount},
        mono_ms=mono_ms,
    )


def _transfer_out(guild_id: str, player_id: str, stack_id: str, mono_ms: int = 0) -> tuple[int, dict]:
    return _request(
        "POST",
        f"/v1/guild/{guild_id}/transfer-out",
        {"player_id": player_id, "stack_id": stack_id},
        mono_ms=mono_ms,
    )


def _interest_run(guild_id: str, period_id: str, mono_ms: int = 0) -> dict:
    status, resp = _request(
        "POST",
        "/v1/admin/interest/run",
        {"guild_id": guild_id, "period_id": period_id},
        mono_ms=mono_ms,
    )
    assert status == 200, resp
    return resp


def _interest_replay(guild_id: str, period_id: str, mono_ms: int = 0) -> dict:
    status, resp = _request(
        "POST",
        "/v1/admin/interest/replay",
        {"guild_id": guild_id, "period_id": period_id},
        mono_ms=mono_ms,
    )
    assert status == 200, resp
    return resp


def _export(guild_id: str, mono_ms: int = 0) -> dict:
    status, body = _request(
        "POST",
        "/v1/guild/export",
        {"guild_id": guild_id},
        mono_ms=mono_ms,
    )
    assert status == 200, body
    assert REPORT.is_file()
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _gold_balance(guild_id: str) -> int:
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT gold_balance FROM guilds WHERE guild_id=?",
            (guild_id,),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def _vault_qty(guild_id: str) -> int:
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM item_stacks WHERE guild_id=?",
            (guild_id,),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def _slice_qty(guild_id: str) -> int:
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM withdraw_slices WHERE guild_id=?",
            (guild_id,),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def daemon_session():
    _reset()
    _build()
    _start_daemon()
    yield
    _stop_daemon()


@pytest.fixture(autouse=True)
def clean_state():
    _reset()
    _start_daemon()
    yield


def test_protected_files_unmodified():
    """Instruction do-not-modify paths (docs, config, fixtures) must stay byte-identical."""
    for rel, expected in PROTECTED_SHA256.items():
        assert _sha256(APP / rel) == expected, rel


def test_partial_stack_withdraw_splits_rows():
    """Partial withdraw must decrement vault and create withdraw_slices row."""
    guild, player, total, partial = scenario_stack_split(SEED)
    _bootstrap(guild, initial_gold_for_seed(SEED))
    stack = _deposit_stack(guild, "guild-ore", total)
    status, body = _withdraw_stack(guild, player, stack["stack_id"], partial, mono_ms=10)
    assert status == 200, body
    assert _vault_qty(guild) == total - partial
    assert _slice_qty(guild) == partial
    report = _export(guild, mono_ms=20)
    assert report["vault_stack_qty"] == total - partial
    assert report["withdrawn_slice_qty"] == partial
    assert report["committed_audit_count"] >= 1
    assert report["orphan_audit_count"] == 0


def test_full_stack_withdraw_removes_vault_row():
    """Full-stack withdraw must delete the vault row and record the full quantity."""
    guild, player, total, _ = scenario_stack_split(SEED)
    _bootstrap(guild, initial_gold_for_seed(SEED))
    stack = _deposit_stack(guild, "guild-ore", total)
    status, body = _withdraw_stack(guild, player, stack["stack_id"], total, mono_ms=10)
    assert status == 200, body
    assert _vault_qty(guild) == 0
    assert _slice_qty(guild) == total
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT COUNT(1) FROM item_stacks WHERE stack_id=?",
            (stack["stack_id"],),
        ).fetchone()
        assert int(row[0]) == 0
    finally:
        conn.close()
    report = _export(guild, mono_ms=20)
    assert report["vault_stack_qty"] == 0
    assert report["withdrawn_slice_qty"] == total
    assert report["committed_audit_count"] >= 1
    assert report["orphan_audit_count"] == 0


def test_concurrent_gold_withdraw_never_negative():
    """Concurrent gold withdraws must not produce negative treasury balance."""
    guild, player, initial, threads, each = scenario_concurrent_gold(SEED)
    _bootstrap(guild, initial)
    results: list[tuple[int, dict]] = []
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = [
            pool.submit(_withdraw_gold, guild, f"{player}-{idx}", each, mono_ms=idx)
            for idx in range(threads)
        ]
        for fut in futures:
            results.append(fut.result(timeout=15))

    balance = _gold_balance(guild)
    assert balance >= 0
    successes = sum(1 for code, _ in results if code == 200)
    failures = sum(1 for code, _ in results if code == 409)
    assert successes + failures == threads
    assert successes >= 1
    expected = initial - successes * each
    assert balance == expected
    assert expected >= 0
    report = _export(guild, mono_ms=100)
    assert report["gold_balance"] == expected
    assert report["gold_balance"] >= 0
    assert report["committed_audit_count"] == successes


def test_rejected_gold_withdraw_leaves_no_committed_audit():
    """Insufficient gold reject must not inflate committed audit count."""
    guild = mutate_id("guild", SEED, "audit")
    player = mutate_id("player", SEED, "audit")
    initial = 500
    _bootstrap(guild, initial)
    status, _ = _withdraw_gold(guild, player, initial + 50, mono_ms=5)
    assert status == 409
    report = _export(guild, mono_ms=10)
    assert report["committed_audit_count"] == 0
    assert report["orphan_audit_count"] == 0
    assert _gold_balance(guild) == initial


def test_successful_gold_withdraw_records_committed_audit():
    """Successful gold withdraw must persist a committed non-orphan audit row."""
    guild = mutate_id("guild", SEED, "audit-ok")
    player = mutate_id("player", SEED, "audit-ok")
    initial = 800
    withdraw = 250
    _bootstrap(guild, initial)
    status, body = _withdraw_gold(guild, player, withdraw, mono_ms=5)
    assert status == 200, body
    assert _gold_balance(guild) == initial - withdraw
    report = _export(guild, mono_ms=10)
    assert report["committed_audit_count"] == 1
    assert report["orphan_audit_count"] == 0
    assert report["gold_balance"] == initial - withdraw


def test_orphan_audit_count_detects_mismatched_payload():
    """Export must count committed audits whose payload disagrees with durable gold."""
    guild = mutate_id("guild", SEED, "orphan")
    player = mutate_id("player", SEED, "orphan")
    initial = 800
    withdraw = 200
    _bootstrap(guild, initial)
    status, body = _withdraw_gold(guild, player, withdraw, mono_ms=5)
    assert status == 200, body
    conn = sqlite3.connect(DB)
    try:
        conn.execute(
            """
            INSERT INTO audit_entries
              (entry_id, guild_id, op_type, payload_json, committed, mono_ms)
            VALUES (?, ?, 'withdraw_gold', ?, 1, ?)
            """,
            (
                "orphan-entry-injected",
                guild,
                json.dumps({"player_id": player, "amount": withdraw, "balance": initial}),
                99,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    report = _export(guild, mono_ms=10)
    assert report["orphan_audit_count"] >= 1
    assert report["committed_audit_count"] >= 2


def test_bound_transfer_out_rejected():
    """Bound stacks cannot transfer out of the vault."""
    guild, player = scenario_bound_transfer(SEED)
    _bootstrap(guild, 1000)
    stack = _deposit_stack(guild, "guild-relic", 1, bound=True)
    status, _ = _transfer_out(guild, player, stack["stack_id"], mono_ms=5)
    assert status == 409
    assert _vault_qty(guild) == 1
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT COUNT(1) FROM player_stacks WHERE guild_id=?",
            (guild,),
        ).fetchone()
        assert int(row[0]) == 0
    finally:
        conn.close()


def test_unbound_transfer_out_moves_stack():
    """Unbound stacks transfer to player_stacks and leave the vault."""
    guild, player = scenario_bound_transfer(SEED)
    _bootstrap(guild, 1000)
    stack = _deposit_stack(guild, "guild-token", 7, bound=False)
    status, body = _transfer_out(guild, player, stack["stack_id"], mono_ms=5)
    assert status == 200, body
    assert _vault_qty(guild) == 0
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT quantity FROM player_stacks WHERE guild_id=? AND player_id=?",
            (guild, player),
        ).fetchone()
        assert row is not None
        assert int(row[0]) == 7
    finally:
        conn.close()


def test_interest_replay_is_idempotent():
    """Run then replay must credit interest exactly once."""
    guild, period, initial, bps = scenario_interest_replay(SEED)
    _bootstrap(guild, initial, bps=bps)
    expected_interest = interest_amount(initial, bps)
    run = _interest_run(guild, period, mono_ms=50)
    assert run["interest_amount"] == expected_interest
    after_run = _gold_balance(guild)
    assert after_run == initial + expected_interest
    _interest_replay(guild, period, mono_ms=60)
    after_replay = _gold_balance(guild)
    assert after_replay == after_run
    report = _export(guild, mono_ms=70)
    assert report["interest_applied_total"] == expected_interest
    assert report["gold_balance"] == initial + expected_interest


def test_interest_run_repeated_is_idempotent():
    """A second interest run for the same period must not double-credit gold."""
    guild, period, initial, bps = scenario_interest_replay(SEED)
    _bootstrap(guild, initial, bps=bps)
    expected_interest = interest_amount(initial, bps)
    run1 = _interest_run(guild, period, mono_ms=50)
    assert run1["interest_amount"] == expected_interest
    after_first = _gold_balance(guild)
    assert after_first == initial + expected_interest
    run2 = _interest_run(guild, period, mono_ms=55)
    assert run2["interest_amount"] == expected_interest
    assert _gold_balance(guild) == after_first
    report = _export(guild, mono_ms=60)
    assert report["interest_applied_total"] == expected_interest
    assert report["gold_balance"] == initial + expected_interest


def test_export_matches_reference_quantities():
    """Audit export quantities match independent vault and slice sums."""
    guild, player, total, partial = scenario_stack_split(SEED)
    gold = initial_gold_for_seed(SEED)
    _bootstrap(guild, gold)
    stack = _deposit_stack(guild, "guild-ore", total)
    _withdraw_stack(guild, player, stack["stack_id"], partial, mono_ms=5)
    report = _export(guild, mono_ms=10)
    assert report["vault_stack_qty"] + report["withdrawn_slice_qty"] == total
    assert report["gold_balance"] == gold


@pytest.mark.parametrize("extra_seed", EXTRA_SEEDS)
def test_seed_variation_blocks_hardcoded_outputs(extra_seed: str):
    """Per-seed stack sizes and interest rates prevent static shortcuts."""
    guild, period, initial, bps = scenario_interest_replay(extra_seed)
    total = stack_qty_for_seed(extra_seed)
    assert total != stack_qty_for_seed(SEED)
    assert initial != initial_gold_for_seed(SEED) or bps != interest_bps_for_seed(SEED)
    _bootstrap(guild, initial, bps=bps)
    _deposit_stack(guild, "guild-ore", total)
    report = _export(guild, mono_ms=1)
    assert report["vault_stack_qty"] == total
    expected_interest = interest_amount(initial, bps)
    _interest_run(guild, period, mono_ms=2)
    report2 = _export(guild, mono_ms=3)
    assert report2["interest_applied_total"] == expected_interest
    bal_after_run = _gold_balance(guild)
    _interest_replay(guild, period, mono_ms=4)
    assert _gold_balance(guild) == bal_after_run
    report3 = _export(guild, mono_ms=5)
    assert report3["interest_applied_total"] == expected_interest


def test_missing_required_field_returns_400():
    """Bootstrap without guild_id is rejected."""
    status, _ = _request("POST", "/v1/guild/bootstrap", {"initial_gold": 100}, mono_ms=0)
    assert status == 400


def test_unknown_stack_withdraw_returns_409():
    """Withdraw against a non-existent stack_id is rejected."""
    guild = mutate_id("guild", SEED, "unk-stack")
    player = mutate_id("player", SEED, "unk-stack")
    _bootstrap(guild, 1000)
    status, _ = _withdraw_stack(guild, player, "nonexistent-stack-id", 1, mono_ms=1)
    assert status == 409


def test_excessive_stack_quantity_returns_409():
    """Withdraw quantity greater than vault stack size is rejected."""
    guild, player, total, _ = scenario_stack_split(SEED)
    _bootstrap(guild, 1000)
    stack = _deposit_stack(guild, "guild-ore", total)
    status, _ = _withdraw_stack(guild, player, stack["stack_id"], total + 1, mono_ms=1)
    assert status == 409
    assert _vault_qty(guild) == total
    assert _slice_qty(guild) == 0
