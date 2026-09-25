"""Build randomized SIP transcript fixtures (anti-hardcoding)."""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

ROOT = Path(os.environ.get("SIPCDR_HIDDEN_ROOT", "/app/fixtures"))


def call_id(rng: random.Random) -> str:
    return f"{rng.randint(100000,999999)}@{rng.choice(['carrier', 'peer', 'trunk'])}.sip"


def tag(rng: random.Random, prefix: str) -> str:
    return f"{prefix}{rng.randint(10000,99999)}"


def write_scenario(slug: str, builder) -> None:
    d = ROOT / slug
    d.mkdir(parents=True, exist_ok=True)
    builder(d)


def dump_log(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")


def default_policy(rng: random.Random) -> dict:
    return {
        "clock_skew_ms": 0,
        "windows": [
            {"name": "peak", "start_minute": 480, "end_minute": 1020, "tier": "peak"},
            {"name": "offpeak", "start_minute": 0, "end_minute": 479, "tier": "offpeak"},
        ],
    }


def invite_answer_bye(d: Path) -> None:
    rng = random.Random(31)
    cid = call_id(rng)
    ft, tt = tag(rng, "f"), tag(rng, "t")
    base = 1_700_000_000_000
    rows = [
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 120, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 180, "branch_id": "z9hG4bK1"},
        {"ts_ms": base + 400, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 200, "branch_id": "z9hG4bK2"},
        {"ts_ms": base + 5000, "direction": "in", "method": "BYE", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 2, "status": 0},
    ]
    dump_log(d / "leg-a.siplog", rows)
    (d / "policy.json").write_text(json.dumps(default_policy(rng), indent=2) + "\n", encoding="utf-8")
    (d / "meta.json").write_text(json.dumps({"call_id": cid, "from_tag": ft, "to_tag": tt}, indent=2) + "\n")


def forked_branch_join(d: Path) -> None:
    rng = random.Random(52)
    cid = call_id(rng)
    ft = tag(rng, "f")
    t1, t2 = tag(rng, "a"), tag(rng, "b")
    base = 1_700_100_000_000
    rows = [
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 50, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": t1, "cseq": 1, "status": 180},
        {"ts_ms": base + 60, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": t2, "cseq": 1, "status": 180},
        {"ts_ms": base + 300, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": t1, "cseq": 1, "status": 200},
        {"ts_ms": base + 2000, "direction": "in", "method": "BYE", "call_id": cid, "from_tag": ft, "to_tag": t1, "cseq": 2, "status": 0},
        {"ts_ms": base + 2500, "direction": "in", "method": "CANCEL", "call_id": cid, "from_tag": ft, "to_tag": t2, "cseq": 3, "status": 0},
    ]
    dump_log(d / "fork.siplog", rows)
    (d / "policy.json").write_text(json.dumps(default_policy(rng), indent=2) + "\n", encoding="utf-8")


def cancel_before_200(d: Path) -> None:
    rng = random.Random(77)
    cid = call_id(rng)
    ft, tt = tag(rng, "f"), tag(rng, "t")
    base = 1_700_200_000_000
    rows = [
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 80, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 183},
        {"ts_ms": base + 200, "direction": "in", "method": "CANCEL", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 2, "status": 0},
        {"ts_ms": base + 350, "direction": "in", "method": "BYE", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 3, "status": 0},
    ]
    dump_log(d / "cancel.siplog", rows)
    (d / "policy.json").write_text(json.dumps(default_policy(rng), indent=2) + "\n", encoding="utf-8")


def provisional_only(d: Path) -> None:
    rng = random.Random(91)
    cid = call_id(rng)
    ft, tt = tag(rng, "f"), tag(rng, "t")
    base = 1_700_300_000_000
    rows = [
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 100, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 180},
        {"ts_ms": base + 500, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 183},
    ]
    dump_log(d / "prov.siplog", rows)
    (d / "policy.json").write_text(json.dumps(default_policy(rng), indent=2) + "\n", encoding="utf-8")


def clock_skew_window(d: Path) -> None:
    rng = random.Random(44)
    cid = call_id(rng)
    ft, tt = tag(rng, "f"), tag(rng, "t")
    skew = 120_000
    pol = default_policy(rng)
    pol["clock_skew_ms"] = skew
    base = 1_698_912_000_000
    rows = [
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 200, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 200},
        {"ts_ms": base + 3000, "direction": "in", "method": "BYE", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 2, "status": 0},
    ]
    dump_log(d / "skew.siplog", rows)
    (d / "policy.json").write_text(json.dumps(pol, indent=2) + "\n", encoding="utf-8")
    (d / "meta.json").write_text(json.dumps({"skew_ms": skew, "expected_tier": "peak"}, indent=2) + "\n")


def retransmit_storm(d: Path) -> None:
    rng = random.Random(63)
    cid = call_id(rng)
    ft, tt = tag(rng, "f"), tag(rng, "t")
    base = 1_700_400_000_000
    rows = [
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 100, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 200},
        {"ts_ms": base + 100, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 200},
        {"ts_ms": base + 150, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 200},
        {"ts_ms": base + 2000, "direction": "in", "method": "BYE", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 2, "status": 0},
    ]
    dump_log(d / "retr.siplog", rows)
    (d / "policy.json").write_text(json.dumps(default_policy(rng), indent=2) + "\n", encoding="utf-8")


def cross_run_idempotent(d: Path) -> None:
    invite_answer_bye(d)


def hidden_cancel_poison(d: Path) -> None:
    rng = random.Random(811)
    cid = call_id(rng)
    ft, tt = tag(rng, "f"), tag(rng, "t")
    base = 1_700_500_000_000
    rows = [
        {"ts_ms": base + 300, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 100, "direction": "in", "method": "CANCEL", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 2, "status": 0},
        {"ts_ms": base + 150, "direction": "in", "method": "BYE", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 3, "status": 0},
    ]
    dump_log(d / "poison.siplog", rows)
    (d / "policy.json").write_text(json.dumps(default_policy(rng), indent=2) + "\n", encoding="utf-8")


def hidden_billing_boundary(d: Path) -> None:
    rng = random.Random(712)
    cid = call_id(rng)
    ft, tt = tag(rng, "f"), tag(rng, "t")
    pol = default_policy(rng)
    base = 1_698_911_880_000
    rows = [
        {"ts_ms": base, "direction": "in", "method": "INVITE", "call_id": cid, "from_tag": ft, "to_tag": "", "cseq": 1, "status": 0},
        {"ts_ms": base + 200, "direction": "out", "method": "", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 1, "status": 200},
        {"ts_ms": base + 5000, "direction": "in", "method": "BYE", "call_id": cid, "from_tag": ft, "to_tag": tt, "cseq": 2, "status": 0},
    ]
    dump_log(d / "bound.siplog", rows)
    (d / "policy.json").write_text(json.dumps(pol, indent=2) + "\n", encoding="utf-8")
    (d / "meta.json").write_text(json.dumps({"expected_tier": "offpeak"}, indent=2) + "\n")


SCENARIOS = {
    "invite-answer-bye": invite_answer_bye,
    "forked-branch-join": forked_branch_join,
    "cancel-before-200": cancel_before_200,
    "provisional-only": provisional_only,
    "clock-skew-window": clock_skew_window,
    "retransmit-storm": retransmit_storm,
    "cross-run-stable-bytes": cross_run_idempotent,
    "hidden-cancel-poison": hidden_cancel_poison,
    "hidden-billing-boundary": hidden_billing_boundary,
}

def main() -> None:
    is_hidden = "SIPCDR_HIDDEN_ROOT" in os.environ
    for slug, fn in SCENARIOS.items():
        if slug.startswith("hidden") and not is_hidden:
            continue
        write_scenario(slug, fn)

if __name__ == "__main__":
    main()
    print("fixtures ok", ROOT)
