"""Independent reference implementation for Maildir/notmuch sync verification."""

from __future__ import annotations

import email
import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

CANONICAL_FLAG_ORDER = "FSRDT"
SYSTEM_TAGS = frozenset({"flagged", "seen", "replied", "trashed", "draft", "inbox"})


@dataclass
class MailRecord:
    message_id: str
    thread_id: str = ""
    maildir_relpath: str = ""
    flags: str = ""
    tags: list[str] = field(default_factory=list)
    keywords_source: str = "none"
    mtime_ns: int = 0
    subject: str = ""
    x_keywords: list[str] = field(default_factory=list)


def normalize_flags(raw: str) -> str:
    letters = {c for c in raw.upper() if c in CANONICAL_FLAG_ORDER}
    return "".join(c for c in CANONICAL_FLAG_ORDER if c in letters)


def split_flags_from_name(name: str) -> tuple[str, str]:
    if ":2," in name:
        base, flags = name.split(":2,", 1)
        return base, flags
    return name, ""


def flag_tags(flags: str) -> list[str]:
    out: list[str] = []
    if "F" in flags:
        out.append("flagged")
    if "S" in flags:
        out.append("seen")
    if "R" in flags:
        out.append("replied")
    if "T" in flags:
        out.append("trashed")
    if "D" in flags:
        out.append("draft")
    return out


def flags_from_tags(tags: list[str]) -> str:
    present: set[str] = set()
    for t in tags:
        if t == "flagged":
            present.add("F")
        elif t == "seen":
            present.add("S")
        elif t == "replied":
            present.add("R")
        elif t == "trashed":
            present.add("T")
        elif t == "draft":
            present.add("D")
    return normalize_flags("".join(present))


def merge_tags(x_keywords: list[str], flag_tag_list: list[str], db_tags: list[str]) -> tuple[list[str], str]:
    source = "none"
    keyword_base: list[str] = []
    if x_keywords:
        keyword_base = list(x_keywords)
        source = "x-keywords"
    elif db_tags:
        keyword_base = [t for t in db_tags if t not in SYSTEM_TAGS]
        if keyword_base:
            source = "db"
    merged = set(keyword_base) | set(flag_tag_list)
    for t in db_tags:
        if t in SYSTEM_TAGS or t in flag_tag_list:
            merged.add(t)
    return sorted(merged), source


def parse_headers(data: bytes) -> tuple[str, str, list[str], list[str], list[str]] | None:
    msg = email.message_from_bytes(data)
    mid = (msg.get("Message-ID") or "").strip()
    if not mid:
        return None
    subject = msg.get("Subject") or ""
    xkw = [k.strip().lower() for k in re.split(r"[\s,]+", msg.get("X-Keywords") or "") if k.strip()]
    refs = [r.strip() for r in re.split(r"\s+", msg.get("References") or "") if r.strip()]
    irt = (msg.get("In-Reply-To") or "").strip()
    return mid, subject, xkw, refs, [irt] if irt else []


def folder_rank(relpath: str) -> int:
    # Prefer cur/ over new/ on mtime ties per message-id-dedupe.md.
    if relpath.startswith("cur/"):
        return 2
    if relpath.startswith("new/"):
        return 1
    return 0


def better(a: MailRecord, b: MailRecord) -> bool:
    if a.mtime_ns != b.mtime_ns:
        return a.mtime_ns > b.mtime_ns
    ra, rb = folder_rank(a.maildir_relpath), folder_rank(b.maildir_relpath)
    if ra != rb:
        return ra > rb
    return a.maildir_relpath > b.maildir_relpath


def dedupe(records: list[MailRecord]) -> tuple[list[MailRecord], int]:
    winners: dict[str, MailRecord] = {}
    dup = 0
    for r in records:
        cur = winners.get(r.message_id)
        if cur is None:
            winners[r.message_id] = r
            continue
        dup += 1
        winners[r.message_id] = r if better(r, cur) else cur
    return list(winners.values()), dup


def bind_threads(records: list[MailRecord], parsed: dict[str, tuple]) -> tuple[list[MailRecord], int]:
    # Union-find with lexicographically smallest Message-ID as component root
    # per message-id-dedupe.md.
    parent: dict[str, str] = {r.message_id: r.message_id for r in records}
    ids = set(parent)

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb

    for r in records:
        meta = parsed.get(r.message_id)
        if not meta:
            continue
        _, _, _, refs, irts = meta
        for irt in irts:
            if irt in ids:
                union(r.message_id, irt)
        for ref in refs:
            if ref in ids:
                union(r.message_id, ref)
    for r in records:
        r.thread_id = find(r.message_id)
    return records, len({r.thread_id for r in records})


def scan_maildir(root: Path, db_path: Path | None) -> tuple[list[MailRecord], dict]:
    files_seen = 0
    skipped = 0
    raw: list[MailRecord] = []
    parsed: dict[str, tuple] = {}
    for folder in ("cur", "new"):
        d = root / folder
        if not d.is_dir():
            continue
        for path in sorted(d.iterdir()):
            if not path.is_file():
                continue
            files_seen += 1
            hdr = parse_headers(path.read_bytes())
            if not hdr:
                skipped += 1
                continue
            mid, subject, xkw, refs, irts = hdr
            relpath = f"{folder}/{path.name}"
            _, flag_raw = split_flags_from_name(path.name)
            rec = MailRecord(
                message_id=mid,
                maildir_relpath=relpath,
                flags=normalize_flags(flag_raw),
                mtime_ns=path.stat().st_mtime_ns,
                subject=subject,
                x_keywords=xkw,
            )
            raw.append(rec)
            parsed[mid] = (mid, subject, xkw, refs, irts)
    con = sqlite3.connect(db_path) if db_path and db_path.is_file() else None
    try:
        for rec in raw:
            db_tags: list[str] = []
            if con:
                row = con.execute(
                    "SELECT tags_json FROM messages WHERE message_id=?", (rec.message_id,)
                ).fetchone()
                if row and row[0]:
                    db_tags = json.loads(row[0])
            ft = flag_tags(rec.flags)
            merged, src = merge_tags(rec.x_keywords, ft, db_tags)
            rec.tags = merged
            rec.keywords_source = src
    finally:
        if con:
            con.close()
    deduped, dup = dedupe(raw)
    bound, threads = bind_threads(deduped, parsed)
    meta = {
        "files_seen": files_seen,
        "messages_in": len(raw),
        "skipped": skipped,
        "duplicates": dup,
        "threads": threads,
    }
    return bound, meta


def build_report(
    records: list[MailRecord],
    meta: dict,
    *,
    commit_before_rename: bool = True,
    flag_renames: int = 0,
    staging_epoch: int = 0,
) -> dict:
    messages = []
    for r in sorted(records, key=lambda x: x.message_id):
        messages.append(
            {
                "message_id": r.message_id,
                "thread_id": r.thread_id,
                "maildir_relpath": r.maildir_relpath,
                "flags": r.flags,
                "tags": sorted(r.tags),
                "keywords_source": r.keywords_source,
            }
        )
    return {
        "sync_version": 1,
        "staging_epoch": staging_epoch,
        "maildir_files_seen": meta["files_seen"],
        "messages_indexed": len(messages),
        "messages_skipped": meta["skipped"],
        "duplicates_merged": meta["duplicates"],
        "flag_renames": flag_renames,
        "tag_writes": len(messages),
        "threads_resolved": meta["threads"],
        "commit_before_rename": commit_before_rename,
        "messages": messages,
    }


def get_staging_epoch(db_path: Path | None) -> int:
    if not db_path or not db_path.is_file():
        return 0
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT value FROM sync_meta WHERE key='staging_epoch'").fetchone()
        return int(row[0]) if row else 0
    finally:
        con.close()


def bump_staging_epoch(db_path: Path) -> int:
    con = sqlite3.connect(db_path)
    try:
        cur = get_staging_epoch(db_path)
        nxt = cur + 1
        con.execute(
            "INSERT INTO sync_meta(key,value) VALUES('staging_epoch',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(nxt),),
        )
        con.commit()
        return nxt
    finally:
        con.close()


def reference_sync(root: Path, db_path: Path | None = None) -> dict:
    records, meta = scan_maildir(root, db_path)
    renames = 0
    for rec in records:
        want = flags_from_tags(rec.tags)
        folder = str(Path(rec.maildir_relpath).parent).replace("\\", "/")
        base, _ = split_flags_from_name(Path(rec.maildir_relpath).name)
        if want:
            new_rel = f"{folder}/{base}:2,{want}"
        else:
            new_rel = f"{folder}/{base}"
        if rec.maildir_relpath != new_rel:
            renames += 1
            rec.maildir_relpath = new_rel
        rec.flags = want
    # Tests compare against an already-synced DB/maildir; read the committed
    # epoch instead of bumping again (which would desync staging_epoch by +1).
    epoch = get_staging_epoch(db_path) if db_path and db_path.is_file() else 0
    return build_report(records, meta, commit_before_rename=True, flag_renames=renames, staging_epoch=epoch)


def reference_snapshot(root: Path, db_path: Path) -> dict:
    records, meta = scan_maildir(root, db_path)
    entries = []
    for r in records:
        entries.append(
            {
                "message_id": r.message_id,
                "maildir_relpath": r.maildir_relpath,
                "flags": r.flags,
                "x_keywords": list(r.x_keywords),
                "mtime_ns": r.mtime_ns,
                "subject": r.subject,
            }
        )
    return {
        "sync_version": 1,
        "staging_epoch": get_staging_epoch(db_path),
        "maildir_root": str(root),
        "db_path": str(db_path),
        "maildir_files_seen": meta["files_seen"],
        "messages_in": meta["messages_in"],
        "messages_skipped": meta["skipped"],
        "entries": sorted(entries, key=lambda e: e["message_id"]),
    }


def reference_publish(db_path: Path, snapshot_path: Path) -> dict:
    snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT message_id, thread_id, maildir_relpath, flags, tags_json, keywords_source, mtime_ns "
            "FROM messages ORDER BY message_id"
        ).fetchall()
    finally:
        con.close()
    records: list[MailRecord] = []
    for row in rows:
        tags = json.loads(row[4])
        records.append(
            MailRecord(
                message_id=row[0],
                thread_id=row[1],
                maildir_relpath=row[2],
                flags=row[3],
                tags=tags,
                keywords_source=row[5],
                mtime_ns=row[6],
            )
        )
    kw_by_id = {e["message_id"]: e.get("x_keywords") or [] for e in snap.get("entries", [])}
    for rec in records:
        xkw = kw_by_id.get(rec.message_id) or []
        if not xkw:
            continue
        ft = flag_tags(rec.flags)
        merged, src = merge_tags(xkw, ft, rec.tags)
        rec.tags = merged
        rec.keywords_source = src
    meta = {
        "files_seen": snap.get("maildir_files_seen", 0),
        "skipped": snap.get("messages_skipped", 0),
        "duplicates": max(0, snap.get("messages_in", 0) - len(snap.get("entries", []))),
        "threads": len({r.thread_id for r in records}),
    }
    return build_report(
        records,
        meta,
        commit_before_rename=True,
        flag_renames=0,
        staging_epoch=int(snap.get("staging_epoch", 0)),
    )