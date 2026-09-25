"""Verifier contract for bash-lmod-modulefile-conflict-closure-planner.

Maps to instruction.md and /app/docs/*.md contracts. Uses subprocess CLI
and independent reference_* helpers (not grep of /app/lib sources).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

APP = Path("/app")
BIN = APP / "sbin" / "lmodplan"
STATE = APP / "state"
OUTPUT = APP / "output"
FIXTURES = APP / "fixtures"
VERIFIER_FIXTURES = Path("/opt/verifier-fixtures")


def run_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [str(BIN), *args],
        capture_output=True,
        text=True,
        check=False,
        env=merged,
        cwd=str(APP),
    )


def _parse_catalog_dir(catalog: Path) -> list[dict]:
    modules: list[dict] = []
    for path in sorted(catalog.glob("*.mod")) + sorted(catalog.glob("*.module")):
        mod: dict = {
            "name": "",
            "family": "",
            "priority": 0,
            "depends": [],
            "conflicts": [],
            "prepends": [],
            "appends": [],
        }
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            key, _, val = line.partition(" ")
            if key == "@module":
                mod["name"] = val
            elif key == "@family":
                mod["family"] = val
            elif key == "@priority":
                mod["priority"] = int(val)
            elif key in ("@depends", "@requires"):
                mod["depends"].append(val)
            elif key == "@conflict":
                mod["conflicts"].append(val)
            elif key == "@prepend":
                var, _, value = val.partition(" ")
                mod["prepends"].append((var, value))
            elif key == "@append":
                var, _, value = val.partition(" ")
                mod["appends"].append((var, value))
        if not mod["name"]:
            raise ValueError(f"missing module in {path}")
        modules.append(mod)
    return modules


def _record_line(mod: dict) -> str:
    return (
        f"module|{mod['name']}|family={mod['family']}|priority={mod['priority']}"
        f"|depends={','.join(mod['depends'])}|conflicts={','.join(mod['conflicts'])}"
        f"|prepends={'|'.join(f'{a} {b}' for a, b in mod['prepends'])}"
        f"|appends={'|'.join(f'{a} {b}' for a, b in mod['appends'])}"
    )


def reference_catalog_digest(catalog: Path) -> str:
    records = sorted(_record_line(m) for m in _parse_catalog_dir(catalog))
    payload = "\n".join(records)
    return hashlib.sha256(payload.encode()).hexdigest()


def reference_parse_request(req: Path) -> list[str]:
    mods: list[str] = []
    for raw in req.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("load "):
            mods.append(line[5:].strip())
    return mods


def reference_closure(mods: dict[str, dict], requested: list[str]) -> list[str]:
    order: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen or name not in mods:
            return
        seen.add(name)
        for dep in mods[name]["depends"]:
            if dep:
                visit(dep)
        order.append(name)

    for name in requested:
        visit(name)
    return order


def _modules_conflict(a: str, b: str, mods: dict[str, dict]) -> bool:
    return b in mods[a]["conflicts"] or a in mods[b]["conflicts"]


def reference_conflicts(order: list[str], mods: dict[str, dict]) -> tuple[list[str], list[str]]:
    loaded: dict[str, int] = {}
    final: list[str] = []
    unloads: list[str] = []
    for name in order:
        if name not in mods:
            continue
        pri = mods[name]["priority"]
        skip = False
        while True:
            evicted = False
            for other in list(loaded):
                if not _modules_conflict(name, other, mods):
                    continue
                other_pri = mods[other]["priority"]
                if pri > other_pri:
                    del loaded[other]
                    unloads.append(other)
                    if other in final:
                        final.remove(other)
                    evicted = True
                elif pri < other_pri:
                    skip = True
                elif name < other:
                    del loaded[other]
                    unloads.append(other)
                    if other in final:
                        final.remove(other)
                    evicted = True
                else:
                    skip = True
            if skip:
                break
            if not evicted:
                break
        if skip:
            continue
        loaded[name] = pri
        final.append(name)
    return unloads, final


def reference_family_swaps(order: list[str], mods: dict[str, dict]) -> list[str]:
    family_loaded: dict[str, str] = {}
    unloads: list[str] = []
    for name in order:
        fam = mods[name]["family"]
        if not fam:
            continue
        prev = family_loaded.get(fam)
        if prev and prev != name:
            unloads.append(prev)
        family_loaded[fam] = name
    return unloads


def reference_path_mutations(order: list[str], mods: dict[str, dict]) -> list[dict]:
    muts: list[dict] = []
    for name in order:
        for var, val in mods[name]["prepends"]:
            muts.append({"var": var, "op": "prepend", "value": val})
        for var, val in mods[name]["appends"]:
            muts.append({"var": var, "op": "append", "value": val})
    return muts


def reference_materialize_path(muts: list[dict]) -> dict[str, str]:
    prep: dict[str, list[str]] = {}
    app: dict[str, list[str]] = {}
    for m in muts:
        if m["op"] == "prepend":
            prep.setdefault(m["var"], []).append(m["value"])
        else:
            app.setdefault(m["var"], []).append(m["value"])
    out: dict[str, str] = {}
    for var in set(prep) | set(app):
        left = ":".join(reversed(prep.get(var, [])))
        right = ":".join(app.get(var, []))
        if left and right:
            out[var] = f"{left}:{right}"
        elif left:
            out[var] = left
        else:
            out[var] = right
    return out


def reference_resolve(catalog: Path, request: Path) -> dict:
    mods_list = _parse_catalog_dir(catalog)
    mods = {m["name"]: m for m in mods_list}
    requested = reference_parse_request(request)
    closure = reference_closure(mods, requested)
    conflict_unloads, after_conflict = reference_conflicts(closure, mods)
    family_unloads = reference_family_swaps(after_conflict, mods)
    unloads = family_unloads + conflict_unloads
    loads = after_conflict
    muts = reference_path_mutations(loads, mods)
    return {
        "unload_sequence": sorted(set(unloads)),
        "load_sequence": sorted(set(loads)),
        "path_mutations": muts,
        "paths": reference_materialize_path(muts),
        "catalog_digest": reference_catalog_digest(catalog),
    }


def _read_staging(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    sections: dict[str, list[str]] = {}
    current = "_meta"
    sections[current] = []
    for line in text.splitlines():
        if re.match(r"^\[.+\]$", line):
            current = line.strip("[]")
            sections[current] = []
        elif current == "_meta":
            if "=" in line:
                k, v = line.split("=", 1)
                sections.setdefault("_fields", []).append((k, v))
        else:
            if line:
                sections[current].append(line)
    fields = dict(sections.get("_fields", []))
    return {
        "sequence": int(fields.get("sequence", "0")),
        "catalog_digest": fields.get("catalog_digest", ""),
        "unloads": sections.get("unloads", []),
        "loads": sections.get("loads", []),
        "mutations": sections.get("path_mutations", []),
    }


def _pipeline(work: Path, catalog: Path, request: Path, run_id: str) -> dict:
    snap = work / "catalog.snapshot"
    staging = work / "resolve.staging"
    plan = work / "load-plan.json"
    work.mkdir(parents=True, exist_ok=True)
    assert run_cli("ingest", "--catalog", str(catalog), "--out", str(snap)).returncode == 0
    assert run_cli(
        "resolve",
        "--snapshot",
        str(snap),
        "--request",
        str(request),
        "--staging",
        str(staging),
        "--run-id",
        run_id,
    ).returncode == 0
    assert run_cli("export", "--staging", str(staging), "--out", str(plan)).returncode == 0
    return json.loads(plan.read_text(encoding="utf-8"))


def test_cli_ingest_writes_snapshot_schema(tmp_path: Path) -> None:
    """Ingest must write schema_version and catalog_digest headers."""
    snap = tmp_path / "snap"
    proc = run_cli("ingest", "--catalog", str(FIXTURES / "catalogs" / "basic"), "--out", str(snap))
    assert proc.returncode == 0, proc.stderr
    text = snap.read_text(encoding="utf-8")
    assert "schema_version=1" in text
    assert "catalog_digest=" in text


def test_catalog_snapshot_digest_matches_reference(tmp_path: Path) -> None:
    """Catalog digest must use lexicographically sorted module records."""
    catalog = FIXTURES / "catalogs" / "basic"
    snap = tmp_path / "snap"
    run_cli("ingest", "--catalog", str(catalog), "--out", str(snap))
    digest = snap.read_text(encoding="utf-8").splitlines()[1].split("=", 1)[1]
    assert digest == reference_catalog_digest(catalog)


def test_staging_artifact_exists_after_resolve(tmp_path: Path) -> None:
    """Resolve must persist staging snapshot with load and unload sections."""
    snap = tmp_path / "snap"
    staging = tmp_path / "staging"
    catalog = FIXTURES / "catalogs" / "basic"
    req = FIXTURES / "requests" / "basic.req"
    run_cli("ingest", "--catalog", str(catalog), "--out", str(snap))
    proc = run_cli(
        "resolve",
        "--snapshot",
        str(snap),
        "--request",
        str(req),
        "--staging",
        str(staging),
        "--run-id",
        "stg1",
    )
    assert proc.returncode == 0, proc.stderr
    body = staging.read_text(encoding="utf-8")
    assert "[loads]" in body and "[unloads]" in body and "[path_mutations]" in body


def test_basic_load_sequence_dependency_order(tmp_path: Path) -> None:
    """Dependencies must appear before dependents in staging load order."""
    snap = tmp_path / "snap"
    staging = tmp_path / "staging"
    catalog = FIXTURES / "catalogs" / "basic"
    req = FIXTURES / "requests" / "basic.req"
    run_cli("ingest", "--catalog", str(catalog), "--out", str(snap))
    proc = run_cli(
        "resolve",
        "--snapshot",
        str(snap),
        "--request",
        str(req),
        "--staging",
        str(staging),
        "--run-id",
        "dep1",
    )
    assert proc.returncode == 0, proc.stderr
    loads = _read_staging(staging)["loads"]
    assert loads.index("mpi-base/1.0") < loads.index("openmpi/4.1.5")
    assert loads.index("hwloc/2.9") < loads.index("gcc/12.2")


def test_basic_conflict_gcc_higher_priority_wins(tmp_path: Path) -> None:
    """gcc/12.2 must win over gcc/11.3 via conflict precedence."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "gcc-conf")
    assert "gcc/12.2" in plan["load_sequence"]
    assert "gcc/11.3" not in plan["load_sequence"]


def test_requires_alias_in_closure(tmp_path: Path) -> None:
    """@requires must expand closure the same as @depends."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "gcc-only.req", "req-alias")
    assert "hwloc/2.9" in plan["load_sequence"]


def test_family_swap_unloads_prior_compiler(tmp_path: Path) -> None:
    """Family swap must unload gcc/11.3 when gcc/12.2 loads."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "fam1")
    assert "gcc/11.3" in plan["unload_sequence"]


def test_path_prepend_stack_order_for_path(tmp_path: Path) -> None:
    """PATH prepends follow load-order stacking rules from path-mutation-rules.md."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "path1")
    muts = plan["path_mutations"]
    path_vals = [m["value"] for m in muts if m["var"] == "PATH" and m["op"] == "prepend"]
    assert path_vals.index("/opt/openmpi/bin") < path_vals.index("/opt/gcc/12.2/bin")
    ref_paths = reference_materialize_path(muts)
    rendered = ":".join(
        seg
        for seg in ref_paths.get("PATH", "").split(":")
        if seg.startswith("/opt/")
    )
    assert rendered.startswith("/opt/gcc/12.2/bin")


def test_path_append_ld_library_path_chain(tmp_path: Path) -> None:
    """Append mutations accumulate in load order for LD_LIBRARY_PATH."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "ldp1")
    ref = reference_resolve(FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req")
    got = [m for m in plan["path_mutations"] if m["var"] == "LD_LIBRARY_PATH"]
    assert [m["value"] for m in got if m["op"] == "append"] == [
        m["value"] for m in ref["path_mutations"] if m["var"] == "LD_LIBRARY_PATH" and m["op"] == "append"
    ]


def test_export_load_plan_schema_fields(tmp_path: Path) -> None:
    """Export JSON must include schema fields from load-plan-schema.md."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "schema1")
    for key in (
        "schema_version",
        "catalog_digest",
        "sequence",
        "unload_sequence",
        "load_sequence",
        "path_mutations",
        "plan_digest",
    ):
        assert key in plan


def test_export_sequences_lexicographically_sorted(tmp_path: Path) -> None:
    """unload_sequence and load_sequence must be sorted for reproducibility."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "sort1")
    assert plan["unload_sequence"] == sorted(plan["unload_sequence"])
    assert plan["load_sequence"] == sorted(plan["load_sequence"])


def test_plan_digest_stable_on_reexport(tmp_path: Path) -> None:
    """Re-exporting unchanged staging must yield identical plan_digest."""
    snap = tmp_path / "snap"
    staging = tmp_path / "staging"
    out1 = tmp_path / "p1.json"
    out2 = tmp_path / "p2.json"
    catalog = FIXTURES / "catalogs" / "basic"
    req = FIXTURES / "requests" / "basic.req"
    run_cli("ingest", "--catalog", str(catalog), "--out", str(snap))
    run_cli("resolve", "--snapshot", str(snap), "--request", str(req), "--staging", str(staging), "--run-id", "dig1")
    run_cli("export", "--staging", str(staging), "--out", str(out1))
    run_cli("export", "--staging", str(staging), "--out", str(out2))
    d1 = json.loads(out1.read_text(encoding="utf-8"))["plan_digest"]
    d2 = json.loads(out2.read_text(encoding="utf-8"))["plan_digest"]
    assert d1 == d2


def test_resolve_idempotent_same_run_id(tmp_path: Path) -> None:
    """Same run-id and request must keep sequence stable across resolve replay."""
    snap = tmp_path / "snap"
    staging = tmp_path / "staging"
    catalog = FIXTURES / "catalogs" / "basic"
    req = FIXTURES / "requests" / "basic.req"
    run_cli("ingest", "--catalog", str(catalog), "--out", str(snap))
    run_cli("resolve", "--snapshot", str(snap), "--request", str(req), "--staging", str(staging), "--run-id", "idem")
    seq1 = _read_staging(staging)["sequence"]
    run_cli("resolve", "--snapshot", str(snap), "--request", str(req), "--staging", str(staging), "--run-id", "idem")
    seq2 = _read_staging(staging)["sequence"]
    assert seq1 == seq2


def test_cross_run_sequence_bumps_on_request_change(tmp_path: Path) -> None:
    """Changing request file must bump ledger sequence for same run-id."""
    snap = tmp_path / "snap"
    staging = tmp_path / "staging"
    catalog = FIXTURES / "catalogs" / "basic"
    run_cli("ingest", "--catalog", str(catalog), "--out", str(snap))
    run_cli(
        "resolve",
        "--snapshot",
        str(snap),
        "--request",
        str(FIXTURES / "requests" / "basic.req"),
        "--staging",
        str(staging),
        "--run-id",
        "cross",
    )
    seq1 = _read_staging(staging)["sequence"]
    run_cli(
        "resolve",
        "--snapshot",
        str(snap),
        "--request",
        str(FIXTURES / "requests" / "gcc-only.req"),
        "--staging",
        str(staging),
        "--run-id",
        "cross",
    )
    seq2 = _read_staging(staging)["sequence"]
    assert seq2 > seq1


def test_subprocess_full_chain_matches_reference(tmp_path: Path) -> None:
    """End-to-end export must match independent reference resolver."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "ref1")
    ref = reference_resolve(FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req")
    assert plan["load_sequence"] == ref["load_sequence"]
    assert plan["unload_sequence"] == ref["unload_sequence"]


def test_tb3_hidden_mathlib_conflict_chain(tmp_path: Path) -> None:
    """Hidden catalog: fftw vs mkl conflict evicts lower-priority mkl."""
    catalog = VERIFIER_FIXTURES / "catalogs" / "hidden"
    req = VERIFIER_FIXTURES / "requests" / "hidden-math.req"
    plan = _pipeline(tmp_path, catalog, req, "tb3-hidden")
    assert "mkl/2024" in plan["unload_sequence"]
    assert "fftw/3.3" in plan["load_sequence"]
    assert "petsc/3.20" in plan["load_sequence"]


def test_tb3_hidden_petsc_depends_fftw_before_load(tmp_path: Path) -> None:
    """Hidden probe: petsc dependency forces fftw before petsc in load order."""
    catalog = VERIFIER_FIXTURES / "catalogs" / "hidden"
    req = VERIFIER_FIXTURES / "requests" / "hidden-math.req"
    plan = _pipeline(tmp_path, catalog, req, "tb3-dep")
    loads = plan["load_sequence"]
    assert loads.index("fftw/3.3") < loads.index("petsc/3.20")


def test_hidden_export_digest_matches_reference(tmp_path: Path) -> None:
    """Hidden catalog export digest must match reference plan_digest material."""
    catalog = VERIFIER_FIXTURES / "catalogs" / "hidden"
    req = VERIFIER_FIXTURES / "requests" / "hidden-math.req"
    plan = _pipeline(tmp_path, catalog, req, "tb3-dig")
    ref = reference_resolve(catalog, req)
    assert plan["load_sequence"] == ref["load_sequence"]
    assert plan["unload_sequence"] == ref["unload_sequence"]


def test_decoy_wrap_not_required_for_export(tmp_path: Path) -> None:
    """wrap_decoy.sh is optional; export must succeed without calling it."""
    plan = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "decoy1")
    assert plan["plan_digest"]


def test_conflict_only_partial_fails_hidden_mathlib(tmp_path: Path) -> None:
    """Almost-correct: bundled gcc conflict pass must not imply hidden mathlib pass."""
    bundled = _pipeline(tmp_path, FIXTURES / "catalogs" / "basic", FIXTURES / "requests" / "basic.req", "partial")
    hidden_catalog = VERIFIER_FIXTURES / "catalogs" / "hidden"
    hidden_req = VERIFIER_FIXTURES / "requests" / "hidden-math.req"
    ref_hidden = reference_resolve(hidden_catalog, hidden_req)
    assert bundled["load_sequence"] != ref_hidden["load_sequence"]


def test_canonical_catalog_snapshot_path(tmp_path: Path) -> None:
    """Ingest must materialize /app/state/catalog.snapshot when given that out path."""
    snap = STATE / "catalog.snapshot"
    if snap.exists():
        snap.unlink()
    proc = run_cli("ingest", "--catalog", str(FIXTURES / "catalogs" / "basic"), "--out", str(snap))
    assert proc.returncode == 0, proc.stderr
    assert snap.is_file()
    assert "catalog_digest=" in snap.read_text(encoding="utf-8")


def test_canonical_resolve_staging_path(tmp_path: Path) -> None:
    """Resolve must materialize /app/state/resolve.staging when given that staging path."""
    snap = STATE / "catalog.snapshot"
    staging = STATE / "resolve.staging"
    run_cli("ingest", "--catalog", str(FIXTURES / "catalogs" / "basic"), "--out", str(snap))
    proc = run_cli(
        "resolve",
        "--snapshot",
        str(snap),
        "--request",
        str(FIXTURES / "requests" / "basic.req"),
        "--staging",
        str(staging),
        "--run-id",
        "canon-stg",
    )
    assert proc.returncode == 0, proc.stderr
    assert staging.is_file()
    assert "[loads]" in staging.read_text(encoding="utf-8")


def test_canonical_load_plan_output_path(tmp_path: Path) -> None:
    """Export must materialize /app/output/load-plan.json when given that out path."""
    snap = STATE / "catalog.snapshot"
    staging = STATE / "resolve.staging"
    plan = OUTPUT / "load-plan.json"
    run_cli("ingest", "--catalog", str(FIXTURES / "catalogs" / "basic"), "--out", str(snap))
    run_cli(
        "resolve",
        "--snapshot",
        str(snap),
        "--request",
        str(FIXTURES / "requests" / "basic.req"),
        "--staging",
        str(staging),
        "--run-id",
        "canon-out",
    )
    proc = run_cli("export", "--staging", str(staging), "--out", str(plan))
    assert proc.returncode == 0, proc.stderr
    assert plan.is_file()
    body = json.loads(plan.read_text(encoding="utf-8"))
    assert body.get("schema_version") == 1
