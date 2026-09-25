"""Independent reference for amavis-quarantine reconcile."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

APP = Path("/app")
SPAM = APP / "work/spool/spam"
VIRUS = APP / "work/spool/virus"
REL_SPAM = APP / "work/released/spam"
REL_VIRUS = APP / "work/released/virus"
LEDGER = APP / "work/ledger.json"
MANIFEST = APP / "state/spool-manifest.json"
STAGING = APP / "state/release-staging.json"
EPOCH = APP / "state/release-epoch.json"
SEAL = APP / "state/prepare-seal.json"
CUSTODY = APP / "state/custody-journal.jsonl"
SCENARIOS = APP / "fixtures/scenarios"

QID_RE = re.compile(r"Quarantine-ID:\s*([^\s,]+)")
QUEUE_RE = re.compile(r"Queue-ID:\s*([^\s,]+)")


def parse_log(line: str) -> tuple[str, str]:
    qm = QID_RE.search(line)
    if not qm:
        raise ValueError("missing quarantine id")
    qid = qm.group(1)
    pq = QUEUE_RE.search(line)
    queue_id = pq.group(1) if pq else ""
    return qid, queue_id


def spool_for(class_name: str) -> Path:
    return SPAM if class_name == "spam" else VIRUS


def released_for(class_name: str) -> Path:
    return REL_SPAM if class_name == "spam" else REL_VIRUS


def expected_hold_token(seed: str, qid: str) -> str:
    return hashlib.sha256(f"{seed}:{qid}".encode()).hexdigest()[:12]


def compute_policy_digest(manifest_rows: list[dict]) -> str:
    lines: list[str] = []
    for row in manifest_rows:
        qid = row["quarantine_id"]
        sub = row.get("spool_subdir", row.get("stored_class", "spam"))
        meta = APP / "work/spool" / sub / f"msg.{qid}.meta.json"
        if not meta.is_file():
            continue
        mdoc = json.loads(meta.read_text(encoding="utf-8"))
        if "hold_token" in mdoc:
            lines.append(f"{qid}:{mdoc['hold_token']}")
    lines.sort()
    if not lines:
        return ""
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def hold_token_allows(meta: Path | None, seed: str, qid: str) -> bool:
    if meta is None or not meta.is_file():
        return True
    doc = json.loads(meta.read_text(encoding="utf-8"))
    if "hold_token" not in doc:
        return True
    return str(doc["hold_token"]) == expected_hold_token(seed, qid)


def custody_receipt(seed: str, qid: str, seq: int, qclass: str) -> str:
    if qclass == "virus":
        payload = f"{qid}|{seed}|{seq}|{qclass}"
    else:
        payload = f"{seed}|{qid}|{seq}|{qclass}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def custody_root_from_receipts(receipts: list[str]) -> str:
    if not receipts:
        return ""
    return hashlib.sha256("\n".join(receipts).encode()).hexdigest()


def prepare_fingerprint(scenario_label: str, seed: str, policy_digest: str) -> str:
    return hashlib.sha256(f"{scenario_label}:{seed}:{policy_digest}".encode()).hexdigest()[:24]


def ingest_scenario(scenario: str | Path) -> list[dict]:
    scenario_dir = Path(scenario) if str(scenario).startswith("/") else SCENARIOS / str(scenario)
    for d in (SPAM, VIRUS, REL_SPAM, REL_VIRUS):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for cls in ("spam", "virus"):
        src = scenario_dir / "spool" / cls
        if not src.is_dir():
            continue
        for meta in sorted(src.glob("msg.*.meta.json")):
            qid = meta.name.removeprefix("msg.").removesuffix(".meta.json")
            doc = json.loads(meta.read_text(encoding="utf-8"))
            eml = src / f"msg.{qid}.eml"
            if eml.exists():
                shutil.copy2(eml, spool_for(cls) / eml.name)
            shutil.copy2(meta, spool_for(cls) / meta.name)
            rows.append(
                {
                    "quarantine_id": qid,
                    "stored_class": doc.get("class", cls),
                    "spool_subdir": cls,
                    "bytes": int(doc.get("bytes", 0)),
                }
            )
    MANIFEST.write_text(
        json.dumps({"messages": sorted(rows, key=lambda r: r["quarantine_id"])}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return rows


def write_release_staging(
    manifest_rows: list[dict],
    release_epoch: int,
    policy_digest: str,
    fingerprint: str,
) -> None:
    pending: dict[str, list[str]] = {"spam": [], "virus": []}
    index: dict[str, dict] = {}
    for row in manifest_rows:
        qid = row["quarantine_id"]
        sub = row.get("spool_subdir", row.get("stored_class", "spam"))
        stored = row.get("stored_class", sub)
        index[qid] = {"stored_class": stored, "spool_subdir": sub}
        eml = APP / "work/spool" / sub / f"msg.{qid}.eml"
        if eml.is_file() and qid not in pending[stored]:
            pending[stored].append(qid)
    for cls in pending:
        pending[cls] = sorted(pending[cls])
    STAGING.write_text(
        json.dumps(
            {
                "staging_written": False,
                "release_epoch": release_epoch,
                "policy_digest": policy_digest,
                "prepare_fingerprint": fingerprint,
                "pending_in_spool": pending,
                "index": index,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def current_release_epoch() -> int:
    if EPOCH.is_file():
        try:
            return int(json.loads(EPOCH.read_text(encoding="utf-8")).get("epoch", 0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0
    return 0


def order_releases(releases: list[dict], seed: str) -> list[dict]:
    if seed == "alpha01":
        return releases
    return sorted(
        releases,
        key=lambda row: hashlib.sha256(f"{seed}:{parse_log(row['log_line'])[0]}".encode()).hexdigest(),
    )


def locate_eml(qid: str, qclass: str, manifest_rows: list[dict]) -> Path | None:
    by_id = {r["quarantine_id"]: r for r in manifest_rows}
    row = by_id.get(qid)
    if row:
        sub = row.get("spool_subdir", row.get("stored_class", qclass))
        eml = APP / "work/spool" / sub / f"msg.{qid}.eml"
        if eml.is_file():
            return eml
    root = spool_for(qclass)
    eml = root / f"msg.{qid}.eml"
    return eml if eml.is_file() else None


def ledger_released(ledger: dict, qid: str) -> bool:
    return any(e.get("quarantine_id") == qid and e.get("status") == "released" for e in ledger.get("entries", []))


def reference_run(scenario: str | Path, seed: str) -> dict:
    scenario_dir = Path(scenario) if str(scenario).startswith("/") else SCENARIOS / str(scenario)
    scenario_label = scenario_dir.name if str(scenario).startswith("/") else str(scenario)
    requests = json.loads((scenario_dir / "requests.json").read_text(encoding="utf-8"))

    manifest_rows = ingest_scenario(scenario_dir)
    # Expectation uses the epoch file left by the SUT reconcile (do not bump again).
    release_epoch = current_release_epoch()
    policy_digest = compute_policy_digest(manifest_rows)
    fingerprint = prepare_fingerprint(scenario_label, seed, policy_digest)
    write_release_staging(manifest_rows, release_epoch, policy_digest, fingerprint)
    SEAL.write_text(
        json.dumps(
            {
                "scenario": scenario_label,
                "seed": seed,
                "requests_path": str(scenario_dir / "requests.json"),
                "release_epoch": release_epoch,
                "policy_digest": policy_digest,
                "prepare_fingerprint": fingerprint,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    CUSTODY.write_text("", encoding="utf-8")
    ledger = {"next_sequence": 1, "entries": []}
    state = {
        "releases_attempted": 0,
        "releases_succeeded": 0,
        "releases_failed": 0,
        "duplicate_skipped": 0,
        "release_log": [],
    }
    receipts: list[str] = []
    journal_rows: list[dict] = []

    for row in order_releases(requests.get("releases", []), seed):
        log_line = row["log_line"]
        qclass = row["class"]
        state["releases_attempted"] += 1
        try:
            qid, queue_id = parse_log(log_line)
        except ValueError:
            ledger["entries"].append(
                {"quarantine_id": "unknown", "class": qclass, "status": "failed", "queue_id": ""}
            )
            state["releases_failed"] += 1
            state["release_log"].append(
                {"quarantine_id": "unknown", "class": qclass, "status": "failed", "sequence": None}
            )
            continue

        # Policy gate runs before duplicate/locate (matches pipeline.sh).
        eml_for_policy = locate_eml(qid, qclass, manifest_rows)
        meta_for_policy = (
            eml_for_policy.parent / f"msg.{qid}.meta.json" if eml_for_policy else None
        )
        if meta_for_policy is None or not meta_for_policy.is_file():
            for root in (SPAM, VIRUS):
                candidate = root / f"msg.{qid}.meta.json"
                if candidate.is_file():
                    meta_for_policy = candidate
                    break
        if not hold_token_allows(meta_for_policy, seed, qid):
            ledger["entries"].append(
                {"quarantine_id": qid, "class": qclass, "status": "failed", "queue_id": queue_id}
            )
            state["releases_failed"] += 1
            state["release_log"].append(
                {"quarantine_id": qid, "class": qclass, "status": "failed", "sequence": None}
            )
            continue

        if ledger_released(ledger, qid):
            state["duplicate_skipped"] += 1
            state["release_log"].append(
                {"quarantine_id": qid, "class": qclass, "status": "duplicate_skipped", "sequence": None}
            )
            continue

        eml = locate_eml(qid, qclass, manifest_rows)
        meta = eml.parent / f"msg.{qid}.meta.json" if eml else None
        if eml is None or not eml.is_file():
            ledger["entries"].append(
                {"quarantine_id": qid, "class": qclass, "status": "failed", "queue_id": queue_id}
            )
            state["releases_failed"] += 1
            state["release_log"].append(
                {"quarantine_id": qid, "class": qclass, "status": "failed", "sequence": None}
            )
            continue

        dest_root = released_for(qclass)
        dest_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(eml), str(dest_root / eml.name))
        if meta and meta.is_file():
            shutil.move(str(meta), str(dest_root / meta.name))

        seq = int(ledger["next_sequence"])
        ledger["next_sequence"] = seq + 1
        ledger["entries"].append(
            {
                "sequence": seq,
                "quarantine_id": qid,
                "class": qclass,
                "status": "released",
                "queue_id": queue_id,
            }
        )
        receipt = custody_receipt(seed, qid, seq, qclass)
        receipts.append(receipt)
        journal_rows.append(
            {
                "sequence": seq,
                "quarantine_id": qid,
                "class": qclass,
                "receipt": receipt,
            }
        )
        state["releases_succeeded"] += 1
        state["release_log"].append(
            {"quarantine_id": qid, "class": qclass, "status": "released", "sequence": seq}
        )

    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    CUSTODY.write_text(
        "".join(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n" for row in journal_rows),
        encoding="utf-8",
    )

    released_ids = {
        e["quarantine_id"] for e in ledger.get("entries", []) if e.get("status") == "released"
    }
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    pending: dict[str, list[str]] = {"spam": [], "virus": []}
    base = staging.get("pending_in_spool", {})
    for cls in ("spam", "virus"):
        pending[cls] = sorted(q for q in base.get(cls, []) if q not in released_ids)

    tail = 0
    for e in ledger.get("entries", []):
        if e.get("status") == "released" and "sequence" in e:
            tail = max(tail, int(e["sequence"]))

    return {
        "export_version": 1,
        "scenario": scenario_label,
        "seed": seed,
        "releases_attempted": state["releases_attempted"],
        "releases_succeeded": state["releases_succeeded"],
        "releases_failed": state["releases_failed"],
        "duplicate_skipped": state["duplicate_skipped"],
        "ledger_tail_sequence": tail,
        "release_epoch": release_epoch,
        "policy_digest": staging.get("policy_digest", ""),
        "prepare_fingerprint": fingerprint,
        "custody_root": custody_root_from_receipts(receipts),
        "pending_in_spool": pending,
        "release_log": state["release_log"],
    }
