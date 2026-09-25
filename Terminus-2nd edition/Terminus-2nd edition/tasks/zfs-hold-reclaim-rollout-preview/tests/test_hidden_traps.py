"""Hidden verifier overlays for hold salt and depth/txg ordering traps."""

from __future__ import annotations

from pathlib import Path

from zfshold_cli_support import load_compile_publish, reset_state
from zfshold_contract_math import audit_digest, evaluate, load_scenario


HIDDEN = "/opt/verifier-fixtures/zfshold"


def test_hidden_hold_salt_blocks_suffixed_hold() -> None:
    """TB3_HOLD_SALT must suffix holds at load and still block salted snapshot holds."""
    reset_state()
    env = {"TB3_FIXTURE_DIR": HIDDEN, "TB3_HOLD_SALT": "-edge"}
    atlas = load_compile_publish("hidden-hold-salt", "t-salt", env=env)
    inv = load_scenario(
        Path(f"{HIDDEN}/hidden-hold-salt/inventory.json"),
        salt="-edge",
    )
    ref = evaluate(inv)
    assert atlas["audit_digest"] == audit_digest(ref["eligible"])
    blocked = {r["name"]: r["block_reason"] for r in atlas["blocked"]}
    assert blocked.get("edge/svc@held") == "blocked_hold"
    assert "edge/svc@plain" in {r["name"] for r in atlas["eligible"]}
    held = next(ds for ds in inv["datasets"] if ds["name"] == "edge/svc@held")
    assert held["holds"] == ["keep-edge"]


def test_hidden_depth_txg_order() -> None:
    """Hidden overlay must rank deeper snapshots before shallower ones despite txg order."""
    reset_state()
    env = {"TB3_FIXTURE_DIR": HIDDEN}
    atlas = load_compile_publish("hidden-depth-txg", "t-hdepth", env=env)
    names = [r["name"] for r in sorted(atlas["eligible"], key=lambda r: r["reclaim_rank"])]
    assert names == [
        "tank/r/s@beta",
        "tank/r/s@zeta",
        "tank/r@alpha",
        "tank/r@gamma",
    ]
    inv = load_scenario(Path(f"{HIDDEN}/hidden-depth-txg/inventory.json"))
    ref = evaluate(inv)
    assert atlas["audit_digest"] == audit_digest(ref["eligible"])
