"""Verifier for udev device policy compiler — subprocess + udvp_ref_* math only."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path

CLI = Path("/app/lib/cli.sh")
CLI_LAUNCH = ["/bin/bash", str(CLI)]
FIX = Path("/app/fixtures")
VERIFIER_FIX = Path(__file__).resolve().parent / "verifier-fixtures"
STATE_JSON = Path("/app/state/rule_staging.json")
OUT_JSON = Path("/app/output/device_plan.json")
SEQ_TXT = Path("/app/state/replay.seq")
INSTRUCTION_DEVICE_PLAN_PATH = "/app/output/device_plan.json"
INSTRUCTION_REPLAY_SEQ_PATH = "/app/state/replay.seq"


def udvp_spawn(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*CLI_LAUNCH, *args], capture_output=True, text=True, check=False)


def udvp_wipe() -> None:
    for p in (STATE_JSON, OUT_JSON, SEQ_TXT):
        if p.is_file():
            p.unlink()


def udvp_run_ingest_lane(rules: Path, devjson: Path, modtsv: Path, out: Path = STATE_JSON):
    return udvp_spawn(
        "ingest",
        "--rules-dir",
        str(rules),
        "--devices",
        str(devjson),
        "--modalias",
        str(modtsv),
        "--out",
        str(out),
    )


def udvp_run_emit_lane(staging: Path, poljson: Path, out: Path = OUT_JSON):
    return udvp_spawn("export", "--staging", str(staging), "--policy", str(poljson), "--out", str(out))


def _glob(pat: str, val: str) -> bool:
    return fnmatch.fnmatchcase(val, pat)


def _rules_from_dir(rd: Path) -> list[dict]:
    rows: list[dict] = []
    for fi, rf in enumerate(sorted(rd.glob("*.rules"))):
        for ln, raw in enumerate(rf.read_text().splitlines(), 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            pri = 1000 + fi * 100 + ln
            tok: dict = {}
            for part in [p.strip() for p in line.split(",")]:
                if part.startswith('OPTIONS+="priority='):
                    pri = int(part.split("priority=", 1)[1].strip('"'))
                elif part.startswith("ATTR{") and '=="' in part:
                    k, v = part.split('=="', 1)
                    tok[f"ATTR:{k[k.index('{')+1:k.index('}')]}"] = v.rstrip('"')
                elif part.startswith("SYMLINK+="):
                    val = part.split('="', 1)[1].rstrip('"')
                    tok.setdefault("SYMLINK", []).append(val)
                elif '=="' in part:
                    k, v = part.split('=="', 1)
                    tok[k.split("+")[0]] = v.rstrip('"')
                elif '="' in part:
                    k, v = part.split('="', 1)
                    tok[k.split("+")[0]] = v.rstrip('"')
            rows.append(
                {
                    "rule_id": f"{rf.name}:{ln}",
                    "priority": pri,
                    "source_file": rf.name,
                    "line_number": ln,
                    "tokens": tok,
                }
            )
    rows.sort(key=lambda r: (r["priority"], r["source_file"], r["line_number"]))
    return rows


def _modalias_map(p: Path) -> dict[str, str]:
    m: dict[str, str] = {}
    if p.is_file():
        for line in p.read_text().splitlines():
            if line.strip():
                a, b = line.split("\t", 1)
                m[a.strip()] = b.strip()
    return m


def _attrs_merged(devs: list[dict], dev_id: str) -> dict[str, str]:
    by = {d["dev_id"]: d for d in devs}
    chain: list[str] = []
    cur: str | None = dev_id
    seen: set[str] = set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = by.get(cur, {}).get("parent_id")
    out: dict[str, str] = {}
    for cid in reversed(chain):
        out.update(by[cid].get("attrs") or {})
    return out


def _modalias_ok(dm: str, rm: str, cat: dict[str, str]) -> bool:
    if dm == rm or _glob(rm, dm):
        return True
    tag = cat.get(dm)
    if tag and _glob(rm, tag):
        return True
    return any(t == dm and _glob(rm, p) for p, t in cat.items())


def _rule_ok(rule: dict, dev: dict, attrs: dict, cat: dict[str, str]) -> bool:
    t = rule["tokens"]
    if "SUBSYSTEM" in t and t["SUBSYSTEM"] != dev.get("subsystem", ""):
        return False
    if "KERNEL" in t and not _glob(t["KERNEL"], dev.get("kernel", "")):
        return False
    for k, v in t.items():
        if k.startswith("ATTR:") and attrs.get(k[5:], "") != v:
            return False
    if "MODALIAS" in t and not _modalias_ok(dev.get("modalias", ""), t["MODALIAS"], cat):
        return False
    return True


def udvp_compute_ledger(rules_dir: Path, dev_p: Path, mod_p: Path) -> dict:
    doc = json.loads(dev_p.read_text())
    devs = doc["devices"]
    rules = _rules_from_dir(rules_dir)
    cat = _modalias_map(mod_p)
    edges = [
        {
            "dev_id": d["dev_id"],
            "rule_ids": [r["rule_id"] for r in rules if _rule_ok(r, d, _attrs_merged(devs, d["dev_id"]), cat)],
        }
        for d in devs
    ]
    lines: list[str] = []
    for r in rules:
        parts = []
        for k, v in sorted(r["tokens"].items()):
            if isinstance(v, list):
                parts.append(f"{k}={','.join(v)}")
            else:
                parts.append(f"{k}={v}")
        tp = ";".join(parts)
        lines.append(f"{r['rule_id']};{r['priority']};{tp}")
    for d in sorted(devs, key=lambda x: x["dev_id"]):
        ap = ";".join(f"{k}={v}" for k, v in sorted(_attrs_merged(devs, d["dev_id"]).items()))
        lines.append(f"{d['dev_id']};{ap}")
    for e in sorted(edges, key=lambda x: x["dev_id"]):
        lines.append(f"{e['dev_id']};{','.join(e['rule_ids'])}")
    fp = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    return {
        "schema_version": 1,
        "rules": rules,
        "devices": devs,
        "match_edges": edges,
        "staging_digest": fp,
    }


def udvp_compute_plan(ledger: dict, pol_p: Path) -> dict:
    pol = json.loads(pol_p.read_text())
    rb = {r["rule_id"]: r for r in ledger["rules"]}
    rows = []
    cols = []
    for edge in ledger["match_edges"]:
        did, rids = edge["dev_id"], edge["rule_ids"]
        sw: dict[str, str] = {}
        sc: dict[str, list[str]] = {}
        for rid in rids:
            tok = rb[rid]["tokens"]
            sls = tok.get("SYMLINK", [])
            if isinstance(sls, str):
                sls = [sls]
            for sl in sls:
                sc.setdefault(sl, []).append(rid)
                sw[sl] = rid
        for sl, c in sc.items():
            if len(c) > 1:
                cols.append({"symlink": sl, "candidates": c, "winner": sw[sl]})
        o = g = m = ""
        for rid in reversed(rids):
            tk = rb[rid]["tokens"]
            o = o or tk.get("OWNER", "")
            g = g or tk.get("GROUP", "")
            m = m or tk.get("MODE", "")
        o = o or pol.get("default_owner", "root")
        g = g or pol.get("default_group", "root")
        m = m or pol.get("default_mode", "0644")
        m = f"{int(m, 8):04o}"
        rows.append(
            {"dev_id": did, "symlinks": sorted(sw), "owner": o, "group": g, "mode": m, "winning_rules": rids}
        )
    rows.sort(key=lambda x: x["dev_id"])
    cols.sort(key=lambda x: x["symlink"])
    pl = [
        "|".join([d["dev_id"], ",".join(d["symlinks"]), d["owner"], d["group"], d["mode"], ",".join(d["winning_rules"])])
        for d in rows
    ]
    return {"schema_version": 1, "devices": rows, "collisions": cols, "plan_digest": hashlib.sha256("\n".join(pl).encode()).hexdigest()}


def reference_normalize_ledger(*args, **kwargs):
    return udvp_compute_ledger(*args, **kwargs)


def reference_emit_matrix(*args, **kwargs):
    return udvp_compute_plan(*args, **kwargs)


def test_udvp_instruction_named_output_paths():
    """Verify /app/output/device_plan.json and /app/state/replay.seq from instruction."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    udvp_run_emit_lane(STATE_JSON, FIX / "policy.json")
    assert INSTRUCTION_DEVICE_PLAN_PATH == "/app/output/device_plan.json"
    assert INSTRUCTION_REPLAY_SEQ_PATH == "/app/state/replay.seq"
    assert Path(INSTRUCTION_DEVICE_PLAN_PATH).is_file()
    assert Path(INSTRUCTION_REPLAY_SEQ_PATH).is_file()


def test_udvp_cli_binary_present():
    """Verify cli binary present per instruction and /app/docs contracts."""
    assert Path("/app/bin/udev-policy-planner").is_file()
    assert CLI.is_file()


def test_udvp_state_json_materialized():
    """Verify state json materialized per instruction and /app/docs contracts."""
    udvp_wipe()
    assert udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv").returncode == 0
    assert STATE_JSON.is_file()


def test_udvp_output_json_materialized():
    """Verify output json materialized per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    assert udvp_run_emit_lane(STATE_JSON, FIX / "policy.json").returncode == 0
    assert OUT_JSON.is_file()
    assert str(OUT_JSON) == INSTRUCTION_DEVICE_PLAN_PATH


def test_udvp_replay_seq_materialized():
    """Verify replay seq materialized per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    assert SEQ_TXT.is_file() and int(SEQ_TXT.read_text().strip()) >= 1
    assert str(SEQ_TXT) == INSTRUCTION_REPLAY_SEQ_PATH


def test_udvp_staging_snapshot_lane():
    """Verify staging snapshot lane per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    staging = json.loads(STATE_JSON.read_text())
    assert staging.get("staging_digest") and staging.get("match_edges")


def test_udvp_normalize_fingerprint_lane():
    """Verify normalize fingerprint lane per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    got = json.loads(STATE_JSON.read_text())
    ref = udvp_compute_ledger(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    assert got["staging_digest"] == ref["staging_digest"]


def test_udvp_precedence_sort_lane():
    """Verify precedence sort lane per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    rules = json.loads(STATE_JSON.read_text())["rules"]
    keys = [(r["priority"], r["source_file"], r["line_number"]) for r in rules]
    assert keys == sorted(keys)


def test_udvp_binding_edges_lane():
    """Verify binding edges lane per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    got = json.loads(STATE_JSON.read_text())["match_edges"]
    ref = udvp_compute_ledger(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")["match_edges"]
    assert got == ref


def test_udvp_serial_binding_lane():
    """Verify serial binding lane per instruction and /app/docs contracts."""
    ref = udvp_compute_ledger(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    edge = next(e for e in ref["match_edges"] if e["dev_id"] == "disk-a")
    assert any("20-serial" in r for r in edge["rule_ids"])


def test_udvp_modalias_glob_lane():
    """Verify modalias glob lane per instruction and /app/docs contracts."""
    ref = udvp_compute_ledger(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    edge = next(e for e in ref["match_edges"] if e["dev_id"] == "root-hub")
    assert any("30-usb" in r for r in edge["rule_ids"])


def test_udvp_emit_reads_state_only():
    """Verify emit reads state only per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    snap = STATE_JSON.read_bytes()
    seq = SEQ_TXT.read_text().strip()
    assert udvp_run_emit_lane(STATE_JSON, FIX / "policy.json").returncode == 0
    assert STATE_JSON.read_bytes() == snap and SEQ_TXT.read_text().strip() == seq


def test_udvp_emit_matrix_full_lane():
    """Verify emit matrix full lane per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    udvp_run_emit_lane(STATE_JSON, FIX / "policy.json")
    ledger = json.loads(STATE_JSON.read_text())
    assert json.loads(OUT_JSON.read_text()) == udvp_compute_plan(ledger, FIX / "policy.json")


def test_udvp_symlink_arbitration_lane():
    """Verify symlink arbitration lane per instruction and /app/docs contracts."""
    ref = udvp_compute_plan(
        udvp_compute_ledger(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv"),
        FIX / "policy.json",
    )
    w = {c["symlink"]: c["winner"] for c in ref["collisions"]}
    assert w["disk-generic"].startswith("20-serial")


def test_udvp_permission_matrix_lane():
    """Verify permission matrix lane per instruction and /app/docs contracts."""
    ref = udvp_compute_plan(
        udvp_compute_ledger(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv"),
        FIX / "policy.json",
    )
    row = next(d for d in ref["devices"] if d["dev_id"] == "disk-a")
    assert row["group"] == "disk" and row["mode"] == "0660"


def test_udvp_replay_token_bump_lane():
    """Verify replay token bump lane per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    a = int(SEQ_TXT.read_text().strip())
    doc = json.loads((FIX / "devices.json").read_text())
    doc["devices"].append(
        {
            "dev_id": "disk-c",
            "devpath": "/devices/pci0/0-3/block/sdc",
            "parent_id": "root-hub",
            "subsystem": "block",
            "kernel": "sdc",
            "attrs": {},
            "modalias": "block:scsi:disk",
        }
    )
    alt = FIX / "devices-replay-bump.json"
    alt.write_text(json.dumps(doc))
    udvp_run_ingest_lane(FIX / "rules", alt, FIX / "modalias.tsv")
    b = int(SEQ_TXT.read_text().strip())
    alt.unlink()
    assert b == a + 1


def test_udvp_repeat_normalize_stable_bytes():
    """Verify repeat normalize stable bytes per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    b1 = STATE_JSON.read_bytes()
    s1 = SEQ_TXT.read_text().strip()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    assert STATE_JSON.read_bytes() == b1 and SEQ_TXT.read_text().strip() == s1


def test_udvp_repeat_emit_stable_bytes():
    """Verify repeat emit stable bytes per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    udvp_run_emit_lane(STATE_JSON, FIX / "policy.json")
    b1 = OUT_JSON.read_bytes()
    udvp_run_emit_lane(STATE_JSON, FIX / "policy.json")
    assert OUT_JSON.read_bytes() == b1


def test_tb3_udvp_optfixture_i2c_normalize_lane():
    """Verify TB3 optfixture i2c normalize lane per instruction and /app/docs contracts."""
    udvp_wipe()
    r = VERIFIER_FIX / "rules"
    assert udvp_run_ingest_lane(r, VERIFIER_FIX / "devices.json", VERIFIER_FIX / "modalias.tsv").returncode == 0
    got = json.loads(STATE_JSON.read_text())
    ref = udvp_compute_ledger(r, VERIFIER_FIX / "devices.json", VERIFIER_FIX / "modalias.tsv")
    assert got["staging_digest"] == ref["staging_digest"]


def test_tb3_udvp_optfixture_emit_rows_lane():
    """Verify TB3 optfixture emit rows lane per instruction and /app/docs contracts."""
    udvp_wipe()
    r = VERIFIER_FIX / "rules"
    udvp_run_ingest_lane(r, VERIFIER_FIX / "devices.json", VERIFIER_FIX / "modalias.tsv")
    udvp_run_emit_lane(STATE_JSON, VERIFIER_FIX / "policy.json")
    got = json.loads(OUT_JSON.read_text())
    ref = udvp_compute_plan(
        udvp_compute_ledger(r, VERIFIER_FIX / "devices.json", VERIFIER_FIX / "modalias.tsv"),
        VERIFIER_FIX / "policy.json",
    )
    assert got["devices"] == ref["devices"]


def test_tb3_udvp_optfixture_symlink_lane():
    """Verify hidden udvp optfixture symlink lane per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(
        VERIFIER_FIX / "rules",
        VERIFIER_FIX / "devices.json",
        VERIFIER_FIX / "modalias.tsv",
    )
    udvp_run_emit_lane(STATE_JSON, VERIFIER_FIX / "policy.json")
    ref = udvp_compute_plan(
        udvp_compute_ledger(
            VERIFIER_FIX / "rules",
            VERIFIER_FIX / "devices.json",
            VERIFIER_FIX / "modalias.tsv",
        ),
        VERIFIER_FIX / "policy.json",
    )
    hidden_doc = json.loads((VERIFIER_FIX / "devices.json").read_text())
    child_id = next(d["dev_id"] for d in hidden_doc["devices"] if d.get("parent_id"))
    got = json.loads(OUT_JSON.read_text())
    got_row = next(d for d in got["devices"] if d["dev_id"] == child_id)
    ref_row = next(d for d in ref["devices"] if d["dev_id"] == child_id)
    assert got_row["symlinks"] == ref_row["symlinks"]


def test_udvp_spawn_rejects_missing_args():
    """Verify spawn rejects missing args per instruction and /app/docs contracts."""
    udvp_wipe()
    assert udvp_spawn("ingest").returncode != 0


def test_udvp_rows_lex_sorted():
    """Verify rows lex sorted per instruction and /app/docs contracts."""
    udvp_wipe()
    udvp_run_ingest_lane(FIX / "rules", FIX / "devices.json", FIX / "modalias.tsv")
    udvp_run_emit_lane(STATE_JSON, FIX / "policy.json")
    ids = [d["dev_id"] for d in json.loads(OUT_JSON.read_text())["devices"]]
    assert ids == sorted(ids)
