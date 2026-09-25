"""Behavioral verifier for guild bank treasury ops ledger."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_bank import (
    initial_gold_for_seed,
    interest_amount,
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
PATCHES = Path(__file__).resolve().parent / "patches"

PATCH_TARGETS = {
    "store": APP / "internal/store/store.go",
    "dao": APP / "internal/bank/dao.go",
    "withdraw": APP / "internal/bank/withdraw.go",
    "transfer": APP / "internal/bank/transfer.go",
    "accrual": APP / "internal/interest/accrual.go",
}

PATCH_MODULES = tuple(PATCH_TARGETS.keys())
# Verifier-side baseline digests (shipping environment tree). Not computed at import time.
PROTECTED_SHA256: dict[str, str] = {
    "config/guildbank.json": "d511e7d23612776ff492898d4771da373ab9d24acd2b90203d03ab7f2ac6d962",
    "docs/bank-contract.md": "774c1aa3036a66da57504862b48d9b782df171993702d6dcda9bdcf9b4001f62",
    "docs/stack-split.md": "ff4ae9eb68cd17d04952f5d59a925a2cb0658377cca30bc21f7321aa558848bb",
    "docs/concurrency.md": "c855c311261f52a4859e4d505e6d2dc1f49e0c37c7f848b0a7040dbc8d950e2f",
    "docs/audit-order.md": "a19050dab64ca0c14a2a06621758127c1aa2eec561fcb76fd7ad1f9da9202ee3",
    "docs/bound-items.md": "126662165aae9ec20be2aeb4d1e0e0dfdea9f1b4827a06b91c8d7b101f758176",
    "docs/interest-journal.md": "a58bc25646a33763961112265c784f13b06adddc847e6aa8e9f9079380f7bd02",
    "docs/export-schema.md": "301d487435bf35a524615a19c1c97a43c9ec4835e38f981ddcfa750bdf18cc7c",
    "docs/fixture-catalog.md": "affc3b97098df0807207a48e7f84d0ffa69b4928a0d7de8da3b8007936a74c51",
    "fixtures/catalog.json": "f349b8463abbee95603bf3a0847663902484384a6253472018172a1b43638bf8",
    "cmd/guildbankd/main.go": "363e096eef515a7894016a64a234a368a10e6e13116c2f1e5857eb1545ec380c",
    "internal/api/server.go": "fd215a6fc3f1a2ac52815d3a5cdfd021855b3089ae1842885411f697c22b1e83",
    "internal/bank/handler.go": "c9ce6f48a312edd2d18e998795ae3c7f1d340f730572ec4c0b387ab6390da619",
    "internal/store/schema.go": "781b7cad14b86018977408c38a087a563ec14fe55d2e1019fc5519b82e561fdb",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd=APP,
        capture_output=True,
        text=True,
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


def restore_shipping_modules() -> None:
    for name in PATCH_MODULES:
        shutil.copy(PATCHES / f"broken_{name}.go", PATCH_TARGETS[name])


@contextmanager
def patched_module(name: str):
    originals = {mod: PATCH_TARGETS[mod].read_text(encoding="utf-8") for mod in PATCH_MODULES}
    try:
        restore_shipping_modules()
        shutil.copy(PATCHES / f"golden_{name}.go", PATCH_TARGETS[name])
        _build()
        yield
    finally:
        for mod, content in originals.items():
            PATCH_TARGETS[mod].write_text(content, encoding="utf-8")
        _build()


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
    """Instruction do-not-modify paths (docs, config, fixtures, wiring) must stay byte-identical."""
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
    assert stack_qty_for_seed(extra_seed) == stack_qty_for_seed(extra_seed)
    _bootstrap(guild, initial, bps=bps)
    total = stack_qty_for_seed(extra_seed)
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


@pytest.mark.parametrize("module_name", ["dao", "withdraw", "transfer", "accrual"])
def test_isolated_module_fix_required(module_name: str):
    """Shipping baseline fails targeted scenarios until each module is repaired."""
    with patched_module(module_name):
        _reset()
        _start_daemon()
        if module_name == "dao":
            guild = mutate_id("guild", SEED, "iso-dao")
            player = mutate_id("player", SEED, "iso-dao")
            _bootstrap(guild, 800)
            status, _ = _withdraw_gold(guild, player, 900, mono_ms=1)
            assert status == 409
            report = _export(guild, mono_ms=2)
            assert report["committed_audit_count"] == 0
        elif module_name == "withdraw":
            guild, player, total, partial = scenario_stack_split(SEED)
            _bootstrap(guild, 1000)
            stack = _deposit_stack(guild, "guild-ore", total)
            status, _ = _withdraw_stack(guild, player, stack["stack_id"], partial, mono_ms=1)
            assert status == 200
            assert _slice_qty(guild) == partial
        elif module_name == "transfer":
            guild, player = scenario_bound_transfer(SEED)
            _bootstrap(guild, 1000)
            stack = _deposit_stack(guild, "guild-relic", 1, bound=True)
            status, _ = _transfer_out(guild, player, stack["stack_id"], mono_ms=1)
            assert status == 409
        else:
            guild, period, initial, bps = scenario_interest_replay(SEED)
            _bootstrap(guild, initial, bps=bps)
            expected = interest_amount(initial, bps)
            _interest_run(guild, period, mono_ms=1)
            bal = _gold_balance(guild)
            _interest_replay(guild, period, mono_ms=2)
            assert _gold_balance(guild) == bal
            report = _export(guild, mono_ms=3)
            assert report["interest_applied_total"] == expected


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
