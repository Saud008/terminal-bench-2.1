"""Fixture catalog builder for formulatrix scenarios — anti-hardcoding via seeded RNG."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

BUNDLED = (
    "ndc-normalize",
    "rxnorm-alias",
    "plan-override",
    "step-chain",
    "date-window",
    "sqlite-dual-refresh",
    "matrix-publish",
    "multi-plan",
)

HIDDEN = (
    "override-precedence-trap",
    "step-chain-boundary-trap",
)


def _rng(scenario: str) -> random.Random:
    seed = int(hashlib.sha256(scenario.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _base_scenario(rng: random.Random, scenario: str) -> dict:
    plan_id = f"PLAN-{rng.randint(100, 999)}"
    drugs = [
        {
            "ndc": f"{rng.randint(1,9999)}-{rng.randint(1,999)}-{rng.randint(1,9)}",
            "rxnorm": "",
            "name": f"Drug-A-{scenario}",
            "aliases": [
                {"code": f"RX{rng.randint(100,199)}", "rank": 1},
                {"code": f"RX{rng.randint(200,299)}", "rank": 3},
            ],
        },
        {
            "ndc": f"{rng.randint(1,9999)}-{rng.randint(1,999)}-{rng.randint(1,9)}",
            "rxnorm": f"RX{rng.randint(300,399)}",
            "name": f"Drug-B-{scenario}",
            "aliases": [],
        },
    ]
    return {
        "scenario": scenario,
        "as_of": "2024-06-15",
        "drugs": drugs,
        "plans": [{"plan_id": plan_id, "name": f"Plan {plan_id}"}],
        "overrides": [],
        "step_chains": [],
    }


def overlay(scenario: str, doc: dict) -> dict:
    drugs = doc["drugs"]
    plan = doc["plans"][0]["plan_id"]
    if scenario == "ndc-normalize":
        drugs[0]["ndc"] = "1234-567-8"
    elif scenario == "rxnorm-alias":
        drugs[0]["rxnorm"] = ""
        drugs[0]["aliases"] = [
            {"code": "RX100", "rank": 2},
            {"code": "RX050", "rank": 5},
            {"code": "RX200", "rank": 5},
        ]
    elif scenario == "plan-override":
        doc["overrides"] = [
            {
                "plan_id": plan,
                "ndc": drugs[0]["ndc"],
                "pa_required": False,
                "priority": 10,
                "effective_start": "2024-01-01",
                "effective_end": "2025-12-31",
            }
        ]
    elif scenario == "step-chain":
        # Three drugs: seq1 blocked, seq2 waived — last-only publishes true; full chain must stay false.
        doc["drugs"].append(
            {
                "ndc": "77-12-3",
                "rxnorm": "RX410",
                "name": f"Drug-C-{scenario}",
                "aliases": [],
            }
        )
        drugs = doc["drugs"]
        doc["step_chains"] = [
            {
                "plan_id": plan,
                "target_ndc": drugs[2]["ndc"],
                "prerequisite_ndc": drugs[0]["ndc"],
                "sequence": 1,
            },
            {
                "plan_id": plan,
                "target_ndc": drugs[2]["ndc"],
                "prerequisite_ndc": drugs[1]["ndc"],
                "sequence": 2,
            },
        ]
        doc["overrides"] = [
            {
                "plan_id": plan,
                "ndc": drugs[1]["ndc"],
                "pa_required": False,
                "priority": 5,
                "effective_start": "2024-01-01",
                "effective_end": "",
            }
        ]
    elif scenario == "date-window":
        # Force raw-string sort to diverge from normalized-NDC sort for roster_digest.
        drugs[0]["ndc"] = "49-814-4"
        drugs[1]["ndc"] = "1088-127-3"
        ndc = drugs[0]["ndc"]
        doc["overrides"] = [
            {
                "plan_id": plan,
                "ndc": ndc,
                "pa_required": True,
                "priority": 5,
                "effective_start": "2024-01-01",
                "effective_end": "",
            },
            {
                "plan_id": plan,
                "ndc": ndc,
                "pa_required": False,
                "priority": 5,
                "effective_start": "2024-06-01",
                "effective_end": "",
            },
        ]
    elif scenario == "sqlite-dual-refresh":
        pass
    elif scenario == "matrix-publish":
        doc["overrides"] = [
            {
                "plan_id": plan,
                "ndc": drugs[0]["ndc"],
                "pa_required": True,
                "priority": 1,
                "effective_start": "2024-01-01",
                "effective_end": "",
            }
        ]
    elif scenario == "multi-plan":
        plan2 = f"PLAN-{int(plan.split('-')[1]) + 1}"
        doc["plans"].append({"plan_id": plan2, "name": f"Plan {plan2}"})
    elif scenario == "override-precedence-trap":
        ndc = drugs[0]["ndc"]
        doc["overrides"] = [
            {
                "plan_id": plan,
                "ndc": ndc,
                "pa_required": True,
                "priority": 20,
                "effective_start": "2024-01-01",
                "effective_end": "",
            },
            {
                "plan_id": plan,
                "ndc": ndc,
                "pa_required": False,
                "priority": 20,
                "effective_start": "2024-06-10",
                "effective_end": "",
            },
            {
                "plan_id": plan,
                "ndc": ndc,
                "pa_required": True,
                "priority": 15,
                "effective_start": "2024-06-01",
                "effective_end": "",
            },
        ]
    elif scenario == "step-chain-boundary-trap":
        # Seq1 blocked (PA true), seq2 waived — last-only incorrectly yields step_complete true.
        doc["drugs"].append(
            {
                "ndc": "55-66-7",
                "rxnorm": "RX420",
                "name": f"Drug-C-{scenario}",
                "aliases": [],
            }
        )
        drugs = doc["drugs"]
        doc["step_chains"] = [
            {
                "plan_id": plan,
                "target_ndc": drugs[2]["ndc"],
                "prerequisite_ndc": drugs[0]["ndc"],
                "sequence": 1,
            },
            {
                "plan_id": plan,
                "target_ndc": drugs[2]["ndc"],
                "prerequisite_ndc": drugs[1]["ndc"],
                "sequence": 2,
            },
        ]
        doc["overrides"] = [
            {
                "plan_id": plan,
                "ndc": drugs[0]["ndc"],
                "pa_required": True,
                "priority": 1,
                "effective_start": "2024-01-01",
                "effective_end": "",
            },
            {
                "plan_id": plan,
                "ndc": drugs[1]["ndc"],
                "pa_required": False,
                "priority": 1,
                "effective_start": "2024-01-01",
                "effective_end": "",
            },
        ]
    return doc


def write_scenario(root: Path, scenario: str) -> None:
    rng = _rng(scenario)
    doc = _base_scenario(rng, scenario)
    doc = overlay(scenario, doc)
    scen_dir = root / "scenarios" / scenario
    scen_dir.mkdir(parents=True, exist_ok=True)
    (scen_dir / "scenario.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    root = Path("/app/fixtures")
    hidden = os.environ.get("FORMULATRIX_HIDDEN_ROOT")
    if hidden:
        root = Path(hidden)
    scenarios = HIDDEN if hidden else BUNDLED
    for scenario in scenarios:
        write_scenario(root, scenario)
    for scen_dir in sorted((root / "scenarios").iterdir()):
        if scen_dir.is_dir() and not (scen_dir / "scenario.json").exists():
            write_scenario(root, scen_dir.name)
    catalog = {
        "root": str(root),
        "scenarios": sorted(p.name for p in (root / "scenarios").iterdir() if p.is_dir()),
    }
    out = root / "data_catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

