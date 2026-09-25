from __future__ import annotations

import hashlib
import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path

BORDERDOC_BIN = "/app/bin/borderdocctl"
APP_ROOT = Path("/app")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")
DECISION_JSON = Path("/app/output/validity-decisions.json")
LEDGER_JSON = Path("/app/output/ledger-manifest.json")
DB_PATH = Path("/app/state/border-validity.db")
PASS_JSON = Path("/app/state/eval-pass.json")
SNAPSHOT_JSON = Path("/app/state/manifest-snapshot.json")
FIXTURE_ROOT = APP_ROOT / "fixtures"
HIDDEN_ROOT = Path("/tests/hidden")
SEED_DIR = Path("/tmp/borderdoc-seed-fixtures")


def borderdoc_cli(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(APP_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset_borderdoc_state() -> None:
    proc = borderdoc_cli(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def derive_doc_id(base: str, seed: str) -> str:
    digest = hashlib.sha256(f"{seed}:{base}".encode()).hexdigest()[:8].upper()
    return f"{base}-{digest}"


def write_seed_scenario(scenario: str, seed: str, source_root: Path) -> Path:
    raw = json.loads((source_root / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))
    sc = deepcopy(raw)
    pass_map: dict[str, str] = {}
    for p in sc.get("passports", []):
        old = p["doc_id"]
        p["doc_id"] = derive_doc_id(old, seed)
        pass_map[old] = p["doc_id"]
    for v in sc.get("visas", []):
        v["doc_id"] = derive_doc_id(v["doc_id"], seed)
        v["passport_id"] = pass_map.get(v["passport_id"], v["passport_id"])
    for st in sc.get("stamps", []):
        st["stamp_id"] = derive_doc_id(st["stamp_id"], seed)
        st["passport_id"] = pass_map.get(st["passport_id"], st["passport_id"])
    out_root = SEED_DIR / seed
    scen_dir = out_root / "scenarios"
    scen_dir.mkdir(parents=True, exist_ok=True)
    (scen_dir / f"{scenario}.json").write_text(json.dumps(sc, indent=2) + "\n", encoding="utf-8")
    return out_root


def full_attest_chain(
    scenario: str,
    fixture_root_path: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root_path or FIXTURE_ROOT
    env: dict[str, str] = {}
    if extra_env:
        env.update(extra_env)
    for step in (
        [BORDERDOC_BIN, "import-manifest", "--scenario", scenario, "--fixture-dir", str(root)],
        [BORDERDOC_BIN, "score-validity", "--scenario", scenario],
        [BORDERDOC_BIN, "commit-ledger", "--scenario", scenario],
    ):
        proc = borderdoc_cli(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def attest_through_scoring(scenario: str, root: Path | None = None) -> None:
    fx = root or FIXTURE_ROOT
    for step in (
        [BORDERDOC_BIN, "import-manifest", "--scenario", scenario, "--fixture-dir", str(fx)],
        [BORDERDOC_BIN, "score-validity", "--scenario", scenario],
    ):
        proc = borderdoc_cli(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def read_decision_report() -> dict:
    return json.loads(DECISION_JSON.read_text(encoding="utf-8"))


# Back-compat aliases for tests mid-migration
invoke = borderdoc_cli
wipe_state = reset_borderdoc_state
materialize_seed_fixtures = write_seed_scenario
run_pipeline = full_attest_chain
run_eval_only = attest_through_scoring
load_decisions = read_decision_report
seed_doc_id = derive_doc_id
