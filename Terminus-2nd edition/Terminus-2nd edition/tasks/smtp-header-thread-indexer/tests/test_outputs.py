"""
Verifier for mailindex SMTP header thread correlation indexer.
"""

from __future__ import annotations

import email
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

APP = Path("/app")
CLI = Path("/usr/local/bin/mailindex")
MAIL = APP / "fixtures/mail"
DB = APP / "data/thread.db"
REPORT = APP / "output/thread-index.json"
SNAPSHOT = APP / "state/thread-index.snapshot.json"
CONTRACT_THREAD_DB = "/app/data/thread.db"
CONTRACT_REPORT = "/app/output/thread-index.json"
CONTRACT_SNAPSHOT = "/app/state/thread-index.snapshot.json"
CONTRACT_SCHEMA = "/app/data/schema.sql"
EXIT_USAGE = 2
TB3_ROOT = Path(os.environ.get("TB3_SMTP_FIXTURES", "/opt/verifier-fixtures"))
RESET = APP / "scripts/reset-state.sh"
TESTS = Path(__file__).resolve().parent
BROKEN = TESTS / "verifier-broken"
GOLDEN = TESTS / "verifier-golden"
PATCH_FILES = {
    "parse.go": APP / "internal/mailparse/parse.go",
    "prepare.go": APP / "internal/thread/prepare.go",
    "link.go": APP / "internal/thread/link.go",
    "root.go": APP / "internal/thread/root.go",
    "assign.go": APP / "internal/thread/assign.go",
    "store.go": APP / "internal/store/store.go",
    "snapshot.go": APP / "internal/staging/snapshot.go",
    "writer.go": APP / "internal/staging/writer.go",
    "publish.go": APP / "internal/export/publish.go",
    "wrap.go": APP / "internal/export/wrap.go",
    "main.go": APP / "cmd/mailindex/main.go",
}

EXPORT_GOLDEN = {
    "snapshot.go": GOLDEN / "golden_snapshot.go",
    "writer.go": GOLDEN / "golden_writer.go",
    "publish.go": GOLDEN / "golden_publish.go",
    "wrap.go": GOLDEN / "golden_wrap.go",
    "main.go": GOLDEN / "golden_main.go",
}

THREAD_GOLDEN = {
    "link.go": GOLDEN / "golden_link.go",
    "root.go": GOLDEN / "golden_root.go",
    "assign.go": GOLDEN / "golden_assign.go",
}

INGEST_GOLDEN = {
    "parse.go": GOLDEN / "golden_parse.go",
    "prepare.go": GOLDEN / "golden_prepare.go",
    **THREAD_GOLDEN,
    "store.go": GOLDEN / "golden_store.go",
}

ANGLE = re.compile(r"<[^>]+>")


@dataclass
class MailMessage:
    message_id: str
    date_unix: int
    subject: str
    in_reply_to: str = ""
    references: list[str] = field(default_factory=list)
    source_file: str = ""
    file_order: int = 0
    message_index: int = 0


def discover_mail_files(root: Path) -> list[str]:
    files = [
        path.relative_to(root).as_posix()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".eml", ".mbox"}
    ]
    return sorted(files)


def first_angle(raw: str) -> str:
    match = ANGLE.search(raw.strip())
    return match.group(0) if match else ""


def parse_reference_ids(raw: str) -> list[str]:
    return [m.group(0) for m in ANGLE.finditer(raw or "")]


def parse_eml_bytes(data: bytes, rel: str, file_order: int, message_index: int) -> MailMessage | None:
    msg = email.message_from_bytes(data)
    message_id = first_angle(msg.get("Message-ID", ""))
    if not message_id:
        return None
    date_raw = msg.get("Date")
    if not date_raw:
        return None
    try:
        when = parsedate_to_datetime(date_raw)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        date_unix = int(when.astimezone(timezone.utc).timestamp())
    except (TypeError, ValueError, OverflowError):
        return None
    subject = msg.get("Subject", "") or ""
    in_reply_to = first_angle(msg.get("In-Reply-To", ""))
    references = parse_reference_ids(msg.get("References", ""))
    return MailMessage(
        message_id=message_id,
        date_unix=date_unix,
        subject=subject,
        in_reply_to=in_reply_to,
        references=references,
        source_file=rel,
        file_order=file_order,
        message_index=message_index,
    )


def split_mbox(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").split("\n")
    parts: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("From ") and current:
            parts.append(current)
            current = [line]
            continue
        current.append(line)
    if current:
        parts.append(current)
    out: list[str] = []
    for block in parts:
        chunk = "\n".join(block).strip()
        if not chunk:
            continue
        if chunk.startswith("From "):
            nl = chunk.find("\n")
            if nl >= 0:
                chunk = chunk[nl + 1 :]
        out.append(chunk)
    return out


def load_mail_dir(root: Path) -> tuple[list[MailMessage], int, int]:
    files = discover_mail_files(root)
    messages: list[MailMessage] = []
    skipped = 0
    for file_order, rel in enumerate(files):
        path = root / Path(rel)
        try:
            data = path.read_bytes()
        except OSError:
            skipped += 1
            continue
        if rel.lower().endswith(".mbox"):
            for message_index, chunk in enumerate(split_mbox(data.decode("utf-8", errors="replace"))):
                parsed = parse_eml_bytes(chunk.encode("utf-8"), rel, file_order, message_index)
                if parsed is None:
                    skipped += 1
                else:
                    messages.append(parsed)
            continue
        parsed = parse_eml_bytes(data, rel, file_order, 0)
        if parsed is None:
            skipped += 1
        else:
            messages.append(parsed)
    return messages, len(files), skipped


def message_newer(a: MailMessage, b: MailMessage) -> bool:
    if a.source_file != b.source_file:
        return a.source_file > b.source_file
    return a.message_index > b.message_index


def prepare(messages: list[MailMessage]) -> tuple[list[MailMessage], int, int]:
    best: dict[str, MailMessage] = {}
    for msg in messages:
        cur = best.get(msg.message_id)
        if cur is None or message_newer(msg, cur):
            best[msg.message_id] = msg
    deduped = sorted(best.values(), key=lambda m: (m.date_unix, m.message_id))
    return deduped, len(messages), len(messages) - len(deduped)


def assign_threads(messages: list[MailMessage]) -> tuple[list[dict], int]:
    ids = {m.message_id: m for m in messages}
    parent = {mid: mid for mid in ids}

    def find(x: str) -> str:
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb

    for msg in messages:
        if msg.in_reply_to and msg.in_reply_to in ids:
            union(msg.message_id, msg.in_reply_to)
        for ref in msg.references:
            if ref in ids:
                union(msg.message_id, ref)

    components: dict[str, list[MailMessage]] = {}
    for mid, msg in ids.items():
        components.setdefault(find(mid), []).append(msg)

    root_for: dict[str, str] = {}
    for comp_key, members in components.items():
        members.sort(key=lambda m: (m.date_unix, m.message_id))
        root_for[comp_key] = members[0].message_id

    indexed: list[dict] = []
    for msg in messages:
        thread_root = root_for[find(msg.message_id)]
        indexed.append(
            {
                "message_id": msg.message_id,
                "thread_root_id": thread_root,
                "date_unix": msg.date_unix,
                "subject": msg.subject,
                "is_root": msg.message_id == thread_root,
            }
        )
    indexed.sort(key=lambda e: (e["date_unix"], e["message_id"]))
    return indexed, len(root_for)


def apply_index(db_path: Path, indexed: list[dict]) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        for row in indexed:
            cur.execute(
                "INSERT OR REPLACE INTO message_threads "
                "(message_id, thread_root_id, date_unix, subject, is_root) VALUES (?, ?, ?, ?, ?)",
                (
                    row["message_id"],
                    row["thread_root_id"],
                    row["date_unix"],
                    row["subject"],
                    1 if row["is_root"] else 0,
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def compute_index(mail_dir: Path, db_path: Path) -> dict:
    messages, files_read, skipped = load_mail_dir(mail_dir)
    prepared, messages_in, deduped = prepare(messages)
    indexed, threads_resolved = assign_threads(prepared)
    apply_index(db_path, indexed)
    return {
        "index_version": 1,
        "files_read": files_read,
        "messages_in": messages_in,
        "messages_indexed": len(indexed),
        "messages_skipped_malformed": skipped,
        "messages_deduped": deduped,
        "threads_resolved": threads_resolved,
        "messages_indexed_list": indexed,
    }


def reference_index_digest(indexed_list: list[dict]) -> str:
    rows = [
        {
            "message_id": row["message_id"],
            "thread_root_id": row["thread_root_id"],
            "date_unix": row["date_unix"],
            "subject": row["subject"],
            "is_root": row["is_root"],
        }
        for row in indexed_list
    ]
    payload = json.dumps(rows, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


def _build() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/mailindex"],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_index(mail_dir: Path, db_path: Path, output: Path = REPORT) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            str(CLI),
            "index",
            "--mail-dir",
            str(mail_dir),
            "--thread-db",
            str(db_path),
            "--output",
            str(output),
        ],
        cwd=APP,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _run_publish(output: Path) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [str(CLI), "publish", "--output", str(output)],
        cwd=APP,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        PATCH_FILES[name].write_text(content, encoding="utf-8")


def with_partial_patch(golden_only: dict[str, Path], fn) -> None:
    saved = {name: path.read_text(encoding="utf-8") for name, path in PATCH_FILES.items()}
    try:
        for name, path in PATCH_FILES.items():
            stem = name.replace(".go", "")
            shutil.copy2(BROKEN / f"broken_{stem}.go", path)
        for name, patch in golden_only.items():
            shutil.copy2(patch, PATCH_FILES[name])
        build = _build()
        assert build.returncode == 0, build.stderr + build.stdout
        fn()
    finally:
        _restore_sources(saved)
        rebuild = _build()
        assert rebuild.returncode == 0, rebuild.stderr + rebuild.stdout


def _row(db_path: Path, message_id: str) -> tuple[str, int, str, int] | None:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT thread_root_id, date_unix, subject, is_root FROM message_threads WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    root, date_unix, subject, is_root = row
    return root, int(date_unix), subject, int(is_root)


class TestMailindexThreadIndexer:
    """Behavioral coverage for SMTP header thread correlation."""

    def setup_method(self) -> None:
        _reset()

    def test_baseline_report_and_db(self) -> None:
        """Default mail tree must match reference index and thread rows."""
        _reset()
        assert _build().returncode == 0
        ref_db = APP / "data" / "verify-ref.db"
        run_db = APP / "data" / "verify-run.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, run_db)
        expected = compute_index(MAIL, ref_db)
        proc = _run_index(MAIL, run_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
        assert actual == expected
        assert CONTRACT_REPORT == "/app/output/thread-index.json"
        assert actual["messages_indexed_list"]
        assert len(actual["messages_indexed_list"]) == actual["messages_indexed"]
        fork = _row(run_db, "<fork@example.com>")
        assert fork is not None and fork[0] == "<fork@example.com>" and fork[3] == 1
        reply = _row(run_db, "<reply@example.com>")
        assert reply is not None and reply[2] == "Duplicated wins"

    def test_schema_sql_applied_to_thread_db(self) -> None:
        """Seeded thread.db must follow /app/data/schema.sql table layout."""
        schema_path = APP / "data" / "schema.sql"
        assert schema_path.is_file()
        assert CONTRACT_SCHEMA == "/app/data/schema.sql"
        assert CONTRACT_THREAD_DB == "/app/data/thread.db"
        assert DB.is_file()
        schema_sql = schema_path.read_text(encoding="utf-8")
        assert "message_threads" in schema_sql
        conn = sqlite3.connect(DB)
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(message_threads)").fetchall()
        }
        conn.close()
        assert {"message_id", "thread_root_id", "date_unix", "subject", "is_root"} <= cols

    def test_index_writes_under_app_data_thread_db(self) -> None:
        """Index must persist rows to the instruction default /app/data/thread.db path."""
        assert _build().returncode == 0
        probe_db = APP / "data" / "thread.db"
        assert str(probe_db) == CONTRACT_THREAD_DB
        ref_db = APP / "data" / "verify-default-path-ref.db"
        shutil.copy(DB, ref_db)
        expected = compute_index(MAIL, ref_db)
        proc = _run_index(MAIL, probe_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        reply = _row(probe_db, "<reply@example.com>")
        assert reply is not None and reply[2] == "Duplicated wins"
        assert CONTRACT_THREAD_DB == "/app/data/thread.db"

    def test_duplicate_message_id_later_file_wins(self) -> None:
        """Duplicate Message-ID across files must keep the lexicographically later path."""
        work = APP / "data" / "msg-cross-file"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        (work / "001-first.eml").write_text(
            "Message-ID: <dup-cross@example.com>\nDate: Wed, 03 Jan 2024 09:00:00 +0000\nSubject: Old subject\nFrom: a@example.com\n\nOld body.",
            encoding="utf-8",
        )
        (work / "010-second.eml").write_text(
            "Message-ID: <dup-cross@example.com>\nDate: Wed, 03 Jan 2024 09:05:00 +0000\nSubject: New subject wins\nFrom: b@example.com\n\nNew body.",
            encoding="utf-8",
        )
        ref_db = APP / "data" / "verify-cross-file-ref.db"
        work_db = APP / "data" / "verify-cross-file.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        expected = compute_index(work, ref_db)
        assert _build().returncode == 0
        proc = _run_index(work, work_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        row = _row(work_db, "<dup-cross@example.com>")
        assert row is not None and row[2] == "New subject wins"

    def test_same_file_duplicate_message_id_last_wins(self) -> None:
        """Duplicate Message-ID within one mbox file must keep the last message in file order."""
        work = APP / "data" / "msg-same-file"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        (work / "001-base.mbox").write_text(
            "From mailindex@example.com Wed, 03 Jan 2024 10:00:00 2024\nMessage-ID: <dup-same@example.com>\nDate: Wed, 03 Jan 2024 10:00:00 +0000\nSubject: First\nFrom: a@example.com\n\nFirst body.\nFrom mailindex@example.com Wed, 03 Jan 2024 10:01:00 2024\nMessage-ID: <dup-same@example.com>\nDate: Wed, 03 Jan 2024 10:01:00 +0000\nSubject: Last wins\nFrom: b@example.com\n\nLast body.",
            encoding="utf-8",
        )
        ref_db = APP / "data" / "verify-same-file-ref.db"
        work_db = APP / "data" / "verify-same-file.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        expected = compute_index(work, ref_db)
        assert _build().returncode == 0
        proc = _run_index(work, work_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        row = _row(work_db, "<dup-same@example.com>")
        assert row is not None and row[2] == "Last wins"

    def test_thread_root_earliest_date(self) -> None:
        """Connected thread must use earliest Date as thread root."""
        _reset()
        assert _build().returncode == 0
        ref_db = APP / "data" / "verify-root-ref.db"
        work_db = APP / "data" / "verify-root.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        expected = compute_index(MAIL, ref_db)
        proc = _run_index(MAIL, work_db)
        assert proc.returncode == 0
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        main = [
            e
            for e in report["messages_indexed_list"]
            if e["message_id"] in {"<root@example.com>", "<reply@example.com>", "<mbox-extra@example.com>"}
        ]
        assert main
        assert all(e["thread_root_id"] == "<fork@example.com>" for e in main)

    def test_secondary_reference_links_when_first_missing(self) -> None:
        """References must union every listed ID, not only the first token."""
        work = APP / "data" / "refs-secondary"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        (work / "001-anchor.eml").write_text(
            "Message-ID: <anchor@example.com>\nDate: Fri, 05 Jan 2024 08:00:00 +0000\nSubject: Anchor\nFrom: anchor@example.com\n\nAnchor body.",
            encoding="utf-8",
        )
        (work / "002-middle.eml").write_text(
            "Message-ID: <middle@example.com>\nDate: Fri, 05 Jan 2024 09:00:00 +0000\nSubject: Middle\nReferences: <anchor@example.com>\nFrom: middle@example.com\n\nMiddle body.",
            encoding="utf-8",
        )
        (work / "003-leaf.eml").write_text(
            "Message-ID: <leaf@example.com>\nDate: Fri, 05 Jan 2024 10:00:00 +0000\nSubject: Leaf\nReferences: <missing@example.com> <middle@example.com>\nFrom: leaf@example.com\n\nLeaf body.",
            encoding="utf-8",
        )
        ref_db = APP / "data" / "verify-secondary-ref.db"
        work_db = APP / "data" / "verify-secondary.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        expected = compute_index(work, ref_db)
        assert _build().returncode == 0
        proc = _run_index(work, work_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        leaf = _row(work_db, "<leaf@example.com>")
        assert leaf is not None and leaf[0] == "<anchor@example.com>" and leaf[3] == 0

    def test_references_only_thread_link(self) -> None:
        """References without In-Reply-To must still join an existing thread."""
        work = APP / "data" / "refs-only"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        (work / "001-root.eml").write_text(
            "Message-ID: <refs-root@example.com>\nDate: Thu, 04 Jan 2024 08:00:00 +0000\nSubject: Refs root\nFrom: root@example.com\n\nRoot.",
            encoding="utf-8",
        )
        (work / "002-child.eml").write_text(
            "Message-ID: <refs-child@example.com>\nDate: Thu, 04 Jan 2024 09:00:00 +0000\nSubject: Refs child\nReferences: <refs-root@example.com>\nFrom: child@example.com\n\nChild.",
            encoding="utf-8",
        )
        ref_db = APP / "data" / "verify-refs-ref.db"
        work_db = APP / "data" / "verify-refs.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        expected = compute_index(work, ref_db)
        assert _build().returncode == 0
        proc = _run_index(work, work_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        child = _row(work_db, "<refs-child@example.com>")
        assert child is not None and child[0] == "<refs-root@example.com>" and child[3] == 0

    def test_separate_thread_side_branch(self) -> None:
        """Unlinked messages must form their own thread root."""
        _reset()
        assert _build().returncode == 0
        ref_db = APP / "data" / "verify-side-ref.db"
        work_db = APP / "data" / "verify-side.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        expected = compute_index(MAIL, ref_db)
        proc = _run_index(MAIL, work_db)
        assert proc.returncode == 0
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        row = _row(work_db, "<side@example.com>")
        assert row is not None and row[0] == "<side@example.com>" and row[3] == 1
        linked = _row(work_db, "<reply@example.com>")
        assert linked is not None and linked[0] == "<fork@example.com>"

    def test_verifier_seed_extra_message(self) -> None:
        """VERIFIER_SEED must add mail fragments replayed live, not hardcoded JSON."""
        _reset()
        seed = os.environ.get("VERIFIER_SEED", "smtp-header-thread-indexer")
        token = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
        work_dir = APP / "data" / f"mail-{token}"
        ref_db = APP / "data" / f"thread-ref-{token}.db"
        work_db = APP / "data" / f"thread-{token}.db"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        shutil.copytree(MAIL, work_dir)
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        msg_id = f"<seed-{token}@example.com>"
        extra = work_dir / f"050-seed-{token}.eml"
        extra.write_text(
            "\n".join(
                [
                    f"Message-ID: {msg_id}",
                    "Date: Wed, 03 Jan 2024 08:00:00 +0000",
                    f"Subject: Seed {token}",
                    "From: seed@example.com",
                    "",
                    "Seed body.",
                ]
            ),
            encoding="utf-8",
        )
        expected = compute_index(work_dir, ref_db)
        assert _build().returncode == 0
        proc = _run_index(work_dir, work_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        assert any(e["message_id"] == msg_id for e in report["messages_indexed_list"])

    def test_missing_mail_dir_exit_two(self) -> None:
        """Missing mail directory must exit 2."""
        _reset()
        assert _build().returncode == 0
        missing = APP / "data/missing-mail"
        proc = _run_index(missing, APP / "data/thread.db")
        assert proc.returncode == EXIT_USAGE

    def test_mail_path_not_directory_exit_two(self) -> None:
        """Mail path that is a regular file must exit 2."""
        _reset()
        assert _build().returncode == 0
        file_path = APP / "data/not-a-directory.eml"
        file_path.write_text("Message-ID: <x@example.com>\n\n", encoding="utf-8")
        proc = _run_index(file_path, APP / "data/thread.db")
        assert proc.returncode == EXIT_USAGE

    def test_thread_db_open_failure(self) -> None:
        """TB3 missing thread database path must exit 1 without creating a file."""
        _reset()
        assert _build().returncode == 0
        missing_db = APP / "data" / "TB3_missing_thread.db"
        if missing_db.exists():
            missing_db.unlink()
        proc = _run_index(MAIL, missing_db)
        assert proc.returncode == 1
        assert not missing_db.exists()

    def test_partial_golden_prepare_only_still_wrong_thread_root(self) -> None:
        """Correct dedup cannot mask wrong thread-root selection in assign."""
        def check() -> None:
            ref_db = APP / "data" / "verify-partial-prepare-ref.db"
            work_db = APP / "data" / "verify-partial-prepare.db"
            shutil.copy(DB, ref_db)
            shutil.copy(DB, work_db)
            expected = compute_index(MAIL, ref_db)
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            report = json.loads(REPORT.read_text(encoding="utf-8"))
            assert report != expected

        with_partial_patch(
            {
                "prepare.go": GOLDEN / "golden_prepare.go",
                **EXPORT_GOLDEN,
            },
            check,
        )

    def test_partial_golden_assign_only_still_wrong_dedup(self) -> None:
        """Correct threading orchestration cannot mask wrong dedup in prepare."""
        def check() -> None:
            ref_db = APP / "data" / "verify-partial-assign-ref.db"
            work_db = APP / "data" / "verify-partial-assign.db"
            shutil.copy(DB, ref_db)
            shutil.copy(DB, work_db)
            expected = compute_index(MAIL, ref_db)
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            report = json.loads(REPORT.read_text(encoding="utf-8"))
            assert report != expected

        with_partial_patch(
            {
                "assign.go": GOLDEN / "golden_assign.go",
                **EXPORT_GOLDEN,
            },
            check,
        )

    def test_partial_golden_parse_only_still_wrong_thread(self) -> None:
        """Golden parse alone cannot repair thread link or dedup stages."""
        def check() -> None:
            ref_db = APP / "data" / "verify-partial-parse-ref.db"
            work_db = APP / "data" / "verify-partial-parse.db"
            shutil.copy(DB, ref_db)
            shutil.copy(DB, work_db)
            expected = compute_index(MAIL, ref_db)
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            report = json.loads(REPORT.read_text(encoding="utf-8"))
            assert report != expected

        with_partial_patch(
            {
                "parse.go": GOLDEN / "golden_parse.go",
                **EXPORT_GOLDEN,
            },
            check,
        )

    def test_partial_golden_link_only_still_wrong_thread_root(self) -> None:
        """Golden link.go alone cannot mask wrong root selection."""
        def check() -> None:
            ref_db = APP / "data" / "verify-partial-link-ref.db"
            work_db = APP / "data" / "verify-partial-link.db"
            shutil.copy(DB, ref_db)
            shutil.copy(DB, work_db)
            expected = compute_index(MAIL, ref_db)
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            report = json.loads(REPORT.read_text(encoding="utf-8"))
            assert report != expected

        with_partial_patch(
            {
                "parse.go": GOLDEN / "golden_parse.go",
                "prepare.go": GOLDEN / "golden_prepare.go",
                "link.go": GOLDEN / "golden_link.go",
                "assign.go": GOLDEN / "golden_assign.go",
                **EXPORT_GOLDEN,
            },
            check,
        )

    def test_partial_golden_root_only_still_wrong_reference_union(self) -> None:
        """Golden root.go alone cannot mask References union gaps in link.go."""
        work = APP / "data" / "refs-partial-root"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        (work / "001-anchor.eml").write_text(
            "Message-ID: <anchor@example.com>\nDate: Fri, 05 Jan 2024 08:00:00 +0000\nSubject: Anchor\nFrom: anchor@example.com\n\nAnchor body.",
            encoding="utf-8",
        )
        (work / "002-middle.eml").write_text(
            "Message-ID: <middle@example.com>\nDate: Fri, 05 Jan 2024 09:00:00 +0000\nSubject: Middle\nReferences: <anchor@example.com>\nFrom: middle@example.com\n\nMiddle body.",
            encoding="utf-8",
        )
        (work / "003-leaf.eml").write_text(
            "Message-ID: <leaf@example.com>\nDate: Fri, 05 Jan 2024 10:00:00 +0000\nSubject: Leaf\nReferences: <missing@example.com> <middle@example.com>\nFrom: leaf@example.com\n\nLeaf body.",
            encoding="utf-8",
        )

        def check() -> None:
            ref_db = APP / "data" / "verify-partial-root-ref.db"
            work_db = APP / "data" / "verify-partial-root.db"
            shutil.copy(DB, ref_db)
            shutil.copy(DB, work_db)
            expected = compute_index(work, ref_db)
            proc = _run_index(work, work_db)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            report = json.loads(REPORT.read_text(encoding="utf-8"))
            assert report != expected

        try:
            with_partial_patch(
                {
                    "parse.go": GOLDEN / "golden_parse.go",
                    "prepare.go": GOLDEN / "golden_prepare.go",
                    "root.go": GOLDEN / "golden_root.go",
                    "assign.go": GOLDEN / "golden_assign.go",
                    **EXPORT_GOLDEN,
                },
                check,
            )
        finally:
            if work.exists():
                shutil.rmtree(work)

    def test_partial_golden_store_only_still_allows_partial_commit(self) -> None:
        """Correct parse/thread stages cannot mask non-transactional SQLite writes."""
        def check() -> None:
            work_db = APP / "data" / "verify-partial-store.db"
            shutil.copy(DB, work_db)
            conn = sqlite3.connect(work_db)
            conn.execute(
                """
                CREATE TRIGGER abort_thread_insert AFTER INSERT ON message_threads
                FOR EACH ROW
                WHEN (SELECT COUNT(*) FROM message_threads) >= 2
                BEGIN
                  SELECT RAISE(ABORT, 'forced apply failure');
                END
                """
            )
            conn.commit()
            conn.close()
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 1
            conn = sqlite3.connect(work_db)
            count = conn.execute("SELECT COUNT(*) FROM message_threads").fetchone()[0]
            conn.close()
            assert count > 0

        with_partial_patch(
            {
                "parse.go": GOLDEN / "golden_parse.go",
                "prepare.go": GOLDEN / "golden_prepare.go",
                **THREAD_GOLDEN,
                **EXPORT_GOLDEN,
            },
            check,
        )

    def test_batch_transaction_rollback(self) -> None:
        """Mid-batch index failure must roll back all thread rows, not leave partial commits."""
        _reset()
        assert _build().returncode == 0
        work_db = APP / "data" / "verify-rollback.db"
        shutil.copy(DB, work_db)
        conn = sqlite3.connect(work_db)
        conn.execute(
            """
            CREATE TRIGGER abort_thread_insert AFTER INSERT ON message_threads
            FOR EACH ROW
            WHEN (SELECT COUNT(*) FROM message_threads) >= 2
            BEGIN
              SELECT RAISE(ABORT, 'forced apply failure');
            END
            """
        )
        conn.commit()
        conn.close()
        proc = _run_index(MAIL, work_db)
        assert proc.returncode == 1
        assert not REPORT.exists()
        assert not SNAPSHOT.exists()
        conn = sqlite3.connect(work_db)
        count = conn.execute("SELECT COUNT(*) FROM message_threads").fetchone()[0]
        conn.close()
        assert count == 0

    def test_index_writes_snapshot_artifact(self) -> None:
        """Successful index must persist the thread index snapshot before export."""
        _reset()
        assert _build().returncode == 0
        work_db = APP / "data" / "verify-snapshot.db"
        shutil.copy(DB, work_db)
        proc = _run_index(MAIL, work_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert SNAPSHOT.is_file(), "thread-index.snapshot.json missing"
        assert CONTRACT_SNAPSHOT == "/app/state/thread-index.snapshot.json"
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap.get("version") == 1
        assert isinstance(snap.get("messages_indexed_list"), list) and snap["messages_indexed_list"]
        expect_digest = reference_index_digest(snap["messages_indexed_list"])
        assert snap.get("index_digest") == expect_digest

    def test_publish_reads_snapshot_only(self) -> None:
        """Publish must reflect mutated snapshot bytes, not SQLite re-query order."""
        _reset()
        assert _build().returncode == 0
        work_db = APP / "data" / "verify-publish.db"
        shutil.copy(DB, work_db)
        assert _run_index(MAIL, work_db).returncode == 0
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["messages_indexed_list"]
        snap["messages_indexed_list"][0]["subject"] = "mutated-by-snapshot"
        snap["index_digest"] = reference_index_digest(snap["messages_indexed_list"])
        SNAPSHOT.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        out_path = APP / "output" / "snapshot-mutated.json"
        proc = _run_publish(out_path)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        doc = json.loads(out_path.read_text(encoding="utf-8"))
        assert doc["messages_indexed_list"][0]["subject"] == "mutated-by-snapshot"

    def test_publish_without_snapshot_fails(self) -> None:
        """Publish must fail when no index snapshot exists."""
        _reset()
        assert _build().returncode == 0
        work_db = APP / "data" / "verify-no-snapshot.db"
        shutil.copy(DB, work_db)
        assert _run_index(MAIL, work_db).returncode == 0
        SNAPSHOT.unlink()
        proc = _run_publish(APP / "output" / "no-snapshot.json")
        assert proc.returncode != 0

    def test_partial_golden_publish_only_still_reorders_from_sqlite(self) -> None:
        """Golden assign/store cannot hide publish re-querying SQLite instead of snapshot."""
        def check() -> None:
            ref_db = APP / "data" / "verify-partial-publish-ref.db"
            work_db = APP / "data" / "verify-partial-publish.db"
            shutil.copy(DB, ref_db)
            shutil.copy(DB, work_db)
            expected = compute_index(MAIL, ref_db)
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            report = json.loads(REPORT.read_text(encoding="utf-8"))
            assert report != expected

        with_partial_patch(
            {
                **INGEST_GOLDEN,
                "snapshot.go": GOLDEN / "golden_snapshot.go",
                "writer.go": GOLDEN / "golden_writer.go",
                "wrap.go": GOLDEN / "golden_wrap.go",
                "main.go": GOLDEN / "golden_main.go",
            },
            check,
        )

    def test_partial_golden_writer_only_fails_index_digest(self) -> None:
        """Golden snapshot/publish cannot mask wrong index_digest in writer."""
        def check() -> None:
            work_db = APP / "data" / "verify-partial-writer.db"
            shutil.copy(DB, work_db)
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 1, proc.stderr or proc.stdout
            assert SNAPSHOT.is_file()
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            expect = reference_index_digest(snap["messages_indexed_list"])
            assert snap.get("index_digest") != expect

        with_partial_patch(
            {
                **INGEST_GOLDEN,
                "snapshot.go": GOLDEN / "golden_snapshot.go",
                "publish.go": GOLDEN / "golden_publish.go",
                "wrap.go": GOLDEN / "golden_wrap.go",
                "main.go": GOLDEN / "golden_main.go",
            },
            check,
        )

    def test_partial_golden_wrap_only_reorders_snapshot_publish(self) -> None:
        """Golden ingest/store cannot mask wrap re-sorting messages_indexed_list."""
        def check() -> None:
            ref_db = APP / "data" / "verify-partial-wrap-ref.db"
            work_db = APP / "data" / "verify-partial-wrap.db"
            shutil.copy(DB, ref_db)
            shutil.copy(DB, work_db)
            expected = compute_index(MAIL, ref_db)
            proc = _run_index(MAIL, work_db)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            report = json.loads(REPORT.read_text(encoding="utf-8"))
            assert report != expected

        with_partial_patch(
            {
                **INGEST_GOLDEN,
                "snapshot.go": GOLDEN / "golden_snapshot.go",
                "writer.go": GOLDEN / "golden_writer.go",
                "publish.go": GOLDEN / "golden_publish.go",
                "main.go": GOLDEN / "golden_main.go",
            },
            check,
        )

    def test_hidden_angle_tokens_preserved(self) -> None:
        """TB3 bracket-mail under /opt/verifier-fixtures must keep angle-bracket Message-IDs."""
        _reset()
        assert _build().returncode == 0
        hidden_dir = TB3_ROOT / "TB3_mail" / "bracket-mail"
        if not hidden_dir.is_dir():
            hidden_dir = TESTS / "hidden_bundles" / "bracket-mail"
        assert hidden_dir.is_dir(), "missing TB3 bracket-mail bundle"
        ref_db = APP / "data" / "verify-hidden-bracket-ref.db"
        work_db = APP / "data" / "verify-hidden-bracket.db"
        shutil.copy(DB, ref_db)
        shutil.copy(DB, work_db)
        expected = compute_index(hidden_dir, ref_db)
        proc = _run_index(hidden_dir, work_db)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        assert report == expected
        msg_id = "<bracket-hidden@example.com>"
        assert all(entry["message_id"].startswith("<") for entry in report["messages_indexed_list"])
        row = _row(work_db, msg_id)
        assert row is not None
