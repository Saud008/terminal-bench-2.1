"""Independent reference model for guild bank treasury behavior."""

from __future__ import annotations

import hashlib


def seed_offset(seed: str, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
    return int(digest[:8], 16)


def mutate_id(base: str, seed: str, label: str) -> str:
    return f"{base}-{seed_offset(seed, label) & 0xFFFF:04x}"


def stack_qty_for_seed(seed: str) -> int:
    return 20 + (seed_offset(seed, "stack") % 60)


def partial_qty_for_seed(seed: str) -> int:
    total = stack_qty_for_seed(seed)
    return max(1, total // 3)


def interest_bps_for_seed(seed: str) -> int:
    return 100 + (seed_offset(seed, "bps") % 400)


def initial_gold_for_seed(seed: str) -> int:
    return 5000 + (seed_offset(seed, "gold") % 15000)


def interest_amount(balance: int, bps: int) -> int:
    amount = balance * bps // 10000
    return max(1, amount) if balance > 0 else 0


def scenario_stack_split(seed: str) -> tuple[str, str, int, int]:
    guild = mutate_id("guild", seed, "split")
    player = mutate_id("player", seed, "split")
    total = stack_qty_for_seed(seed)
    partial = partial_qty_for_seed(seed)
    return guild, player, total, partial


def scenario_concurrent_gold(seed: str) -> tuple[str, str, int, int, int]:
    guild = mutate_id("guild", seed, "conc")
    player = mutate_id("player", seed, "conc")
    initial = initial_gold_for_seed(seed)
    threads = 6
    each = max(100, initial // 3)
    return guild, player, initial, threads, each


def scenario_bound_transfer(seed: str) -> tuple[str, str]:
    guild = mutate_id("guild", seed, "bound")
    player = mutate_id("player", seed, "bound")
    return guild, player


def scenario_interest_replay(seed: str) -> tuple[str, str, int, int]:
    guild = mutate_id("guild", seed, "int")
    period = f"period-{seed_offset(seed, 'period') & 0xFFFFFF:06x}"
    initial = initial_gold_for_seed(seed)
    bps = interest_bps_for_seed(seed)
    return guild, period, initial, bps
