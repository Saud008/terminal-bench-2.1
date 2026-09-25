#!/usr/bin/env python3
"""Generate bundled amavis quarantine scenario fixtures at image build time."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "scenarios"


def hold_token(seed: str, qid: str) -> str:
    return hashlib.sha256(f"{seed}:{qid}".encode()).hexdigest()[:12]


def log_line(qid: str, queue_id: str, *, spam: bool) -> str:
    label = "SPAM" if spam else "INFECTED"
    return (
        f"Mar 10 12:00:01 mail amavis[4242]: (4242-01) Blocked {label}, "
        f"Queue-ID: {queue_id}, mail_id: mid-{qid}, Quarantine-ID: {qid}, Hits: 7.1"
    )


def write_message(
    scenario_dir: Path,
    qclass: str,
    qid: str,
    queue_id: str,
    body: str,
    *,
    hold_token_value: str | None = None,
) -> None:
    scenario_dir.mkdir(parents=True, exist_ok=True)
    spool = scenario_dir / "spool" / qclass
    spool.mkdir(parents=True, exist_ok=True)
    (spool / f"msg.{qid}.eml").write_text(body + "\n", encoding="utf-8")
    meta = {
        "quarantine_id": qid,
        "class": qclass,
        "queue_id": queue_id,
        "bytes": len(body) + 1,
        "sender": "sender@example.test",
    }
    if hold_token_value is not None:
        meta["hold_token"] = hold_token_value
    (spool / f"msg.{qid}.meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_requests(scenario_dir: Path, releases: list[dict]) -> None:
    scenario_dir.mkdir(parents=True, exist_ok=True)
    doc = {"releases": releases}
    (scenario_dir / "requests.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build() -> None:
    if OUT.exists():
        for child in OUT.iterdir():
            if child.is_dir():
                for p in sorted(child.rglob("*"), reverse=True):
                    if p.is_file():
                        p.unlink()
                for p in sorted(child.rglob("*"), reverse=True):
                    if p.is_dir():
                        p.rmdir()
                child.rmdir()

    scenarios: list[dict] = []

    s = OUT / "001-single-spam"
    qid, q = "04Rx-0001-sp", "AAA11101"
    write_message(s, "spam", qid, q, "Subject: spam one")
    write_requests(s, [{"log_line": log_line(qid, q, spam=True), "class": "spam"}])
    scenarios.append({"name": "001-single-spam", "messages": 1})

    s = OUT / "002-single-virus"
    qid, q = "04Rx-0002-vi", "BBB22202"
    write_message(s, "virus", qid, q, "Subject: virus one")
    write_requests(s, [{"log_line": log_line(qid, q, spam=False), "class": "virus"}])
    scenarios.append({"name": "002-single-virus", "messages": 1})

    s = OUT / "003-duplicate-idempotent"
    qid, q = "04Rx-0003-dp", "CCC33303"
    write_message(s, "spam", qid, q, "Subject: dup")
    line = log_line(qid, q, spam=True)
    write_requests(
        s,
        [
            {"log_line": line, "class": "spam"},
            {"log_line": line, "class": "spam"},
        ],
    )
    scenarios.append({"name": "003-duplicate-idempotent", "messages": 1})

    s = OUT / "004-queue-id-trap"
    qid, q = "04Rx-0004-qt", "DDD44404"
    write_message(s, "spam", qid, q, "Subject: trap")
    write_requests(s, [{"log_line": log_line(qid, q, spam=True), "class": "spam"}])
    scenarios.append({"name": "004-queue-id-trap", "messages": 1})

    s = OUT / "005-mixed-batch"
    rows = [
        ("04Rx-0005a-sp", "EEE55505", "spam", True),
        ("04Rx-0005b-vi", "FFF55506", "virus", False),
        ("04Rx-0005c-sp", "GGG55507", "spam", True),
    ]
    releases = []
    for qid, q, cls, is_spam in rows:
        write_message(s, cls, qid, q, f"Subject: {qid}")
        releases.append({"log_line": log_line(qid, q, spam=is_spam), "class": cls})
    write_requests(s, releases)
    scenarios.append({"name": "005-mixed-batch", "messages": 3})

    s = OUT / "006-missing-message"
    qid, q = "04Rx-0006-ms", "HHH66608"
    write_requests(s, [{"log_line": log_line(qid, q, spam=True), "class": "spam"}])
    scenarios.append({"name": "006-missing-message", "messages": 0})

    s = OUT / "007-partial-success"
    good = ("04Rx-0007-ok", "III77709", "spam", True)
    bad = ("04Rx-0007-bad", "JJJ77710", "virus", False)
    releases = []
    for qid, q, cls, is_spam in (good, bad):
        if qid.endswith("ok"):
            write_message(s, cls, qid, q, f"Subject: {qid}")
        releases.append({"log_line": log_line(qid, q, spam=is_spam), "class": cls})
    write_requests(s, releases)
    scenarios.append({"name": "007-partial-success", "messages": 1})

    s = OUT / "008-cross-queue-stress"
    rows = [
        ("04Rx-0008a-sp", "KKK88811", "spam", True),
        ("04Rx-0008b-vi", "LLL88812", "virus", False),
    ]
    releases = []
    for qid, q, cls, is_spam in rows:
        write_message(s, cls, qid, q, f"Subject: {qid}")
        releases.append({"log_line": log_line(qid, q, spam=is_spam), "class": cls})
    write_requests(s, releases)
    scenarios.append({"name": "008-cross-queue-stress", "messages": 2})

    s = OUT / "009-chained-trap"
    good_spam = ("04Rx-0009a-sp", "MMM99913", "spam", True)
    missing_vi = ("04Rx-0009b-vi", "NNN99914", "virus", False)
    good_vi = ("04Rx-0009c-vi", "OOO99915", "virus", False)
    write_message(s, "spam", good_spam[0], good_spam[1], "Subject: chain spam")
    write_message(s, "virus", good_vi[0], good_vi[1], "Subject: chain virus")
    line_spam = log_line(good_spam[0], good_spam[1], spam=True)
    line_missing = log_line(missing_vi[0], missing_vi[1], spam=False)
    line_dup = log_line(good_spam[0], good_spam[1], spam=True)
    line_vi = log_line(good_vi[0], good_vi[1], spam=False)
    write_requests(
        s,
        [
            {"log_line": line_spam, "class": "spam"},
            {"log_line": line_missing, "class": "virus"},
            {"log_line": line_dup, "class": "spam"},
            {"log_line": line_vi, "class": "virus"},
        ],
    )
    scenarios.append({"name": "009-chained-trap", "messages": 2})

    s = OUT / "010-meta-class-trap"
    qid, q = "04Rx-0010-mc", "PPP00016"
    spool = s / "spool" / "spam"
    spool.mkdir(parents=True, exist_ok=True)
    (spool / f"msg.{qid}.eml").write_text("Subject: meta class trap\n", encoding="utf-8")
    meta = {
        "quarantine_id": qid,
        "class": "virus",
        "queue_id": q,
        "bytes": 24,
        "sender": "sender@example.test",
    }
    (spool / f"msg.{qid}.meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_requests(s, [{"log_line": log_line(qid, q, spam=False), "class": "virus"}])
    scenarios.append({"name": "010-meta-class-trap", "messages": 1})

    s = OUT / "011-hold-token-gate"
    qid_ok, q_ok = "04Rx-0011a-ht", "QQQ11117"
    qid_bad, q_bad = "04Rx-0011b-ht", "RRR11118"
    write_message(
        s,
        "spam",
        qid_ok,
        q_ok,
        f"Subject: {qid_ok}",
        hold_token_value=hold_token("alpha01", qid_ok),
    )
    write_message(
        s,
        "spam",
        qid_bad,
        q_bad,
        f"Subject: {qid_bad}",
        hold_token_value="deadbeefcafe",
    )
    write_requests(
        s,
        [
            {"log_line": log_line(qid_ok, q_ok, spam=True), "class": "spam"},
            {"log_line": log_line(qid_bad, q_bad, spam=True), "class": "spam"},
        ],
    )
    scenarios.append({"name": "011-hold-token-gate", "messages": 2})

    s = OUT / "012-custody-class-trap"
    rows = [
        ("04Rx-0012a-sp", "SSS12121", "spam", True),
        ("04Rx-0012b-vi", "TTT12122", "virus", False),
    ]
    releases = []
    for qid, q, cls, is_spam in rows:
        write_message(s, cls, qid, q, f"Subject: {qid}")
        releases.append({"log_line": log_line(qid, q, spam=is_spam), "class": cls})
    write_requests(s, releases)
    scenarios.append({"name": "012-custody-class-trap", "messages": 2})

    catalog = {"scenarios": scenarios}
    (ROOT / "fixtures" / "catalog.json").write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    seeds = {"seeds": ["alpha01", "beta02", "gamma03"]}
    (ROOT / "fixtures" / "seeds.json").write_text(
        json.dumps(seeds, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
