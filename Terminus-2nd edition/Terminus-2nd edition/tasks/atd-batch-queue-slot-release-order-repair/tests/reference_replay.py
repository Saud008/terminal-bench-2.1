"""Independent reference for at-replay scheduling."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

APP = Path("/app")
WORK = APP / "work"
SCRIPTS = WORK / "scripts"
REGISTRY_DIR = WORK / "registry"
SPOOL_DIR = APP / "var/spool/at/jobs"
BATCH_SLOTS = APP / "var/spool/at/batch_slots"
SEQ_FILE = APP / "var/spool/at/.SEQ"
FIXTURES = APP / "fixtures/scenarios"


def job_key(batch_id: str, job_id: str) -> str:
    return f"{batch_id}:{job_id}"


def copy_scenario(scenario_dir: Path) -> None:
    if SCRIPTS.exists():
        shutil.rmtree(SCRIPTS)
    if REGISTRY_DIR.exists():
        shutil.rmtree(REGISTRY_DIR)
    SCRIPTS.mkdir(parents=True)
    REGISTRY_DIR.mkdir(parents=True)
    SPOOL_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_SLOTS.mkdir(parents=True, exist_ok=True)
    for old in SPOOL_DIR.iterdir():
        if old.is_file():
            old.unlink()
    for old in BATCH_SLOTS.iterdir():
        if old.is_file():
            old.unlink()
    src_scripts = scenario_dir / "scripts"
    if src_scripts.is_dir():
        for item in src_scripts.iterdir():
            shutil.copy2(item, SCRIPTS / item.name)
    pre = scenario_dir / "preexisting_spool"
    if pre.is_dir():
        for item in pre.iterdir():
            shutil.copy2(item, SPOOL_DIR / item.name)
    if (scenario_dir / "partial_seq").is_file():
        SEQ_FILE.write_text((scenario_dir / "partial_seq").read_text(encoding="utf-8"), encoding="utf-8")
    else:
        SEQ_FILE.write_text("1\n", encoding="utf-8")


def read_seq() -> int:
    if not SEQ_FILE.is_file():
        return 1
    return int(SEQ_FILE.read_text(encoding="utf-8").strip())


def bump_seq_atomic(current: int) -> int:
    nxt = current + 1
    fd, tmp = tempfile.mkstemp(dir=str(SEQ_FILE.parent), prefix=".SEQ.tmp.")
    os.close(fd)
    Path(tmp).write_text(f"{nxt}\n", encoding="utf-8")
    os.replace(tmp, SEQ_FILE)
    return nxt


def letter_spool_exists(letter: str) -> bool:
    for path in SPOOL_DIR.glob(f"{letter}*"):
        if path.is_file():
            return True
    return False


def allocate_letter(start_letter: str) -> str | None:
    start = ord(start_letter)
    for code in range(start, ord("z") + 1):
        letter = chr(code)
        if (BATCH_SLOTS / letter).is_file():
            continue
        if letter_spool_exists(letter):
            continue
        return letter
    return None


def write_spool(letter: str, seq_val: int, batch: str, job_id: str, atq_epoch: int, script_rel: str) -> str:
    name = f"{letter}{seq_val:010d}"
    body = (SCRIPTS / script_rel).read_text(encoding="utf-8") if (SCRIPTS / script_rel).is_file() else "echo\n"
    header = f"ATQ_EPOCH={atq_epoch} BATCH={batch} JOB={job_id}\n"
    (SPOOL_DIR / name).write_text(header + body, encoding="utf-8")
    (BATCH_SLOTS / letter).touch()
    return name


def complete_spool(name: str, letter: str) -> None:
    (SPOOL_DIR / name).unlink(missing_ok=True)
    (BATCH_SLOTS / letter).unlink(missing_ok=True)


def build_atq_lines() -> list[dict]:
    rows: list[dict] = []
    for path in SPOOL_DIR.iterdir():
        if not path.is_file():
            continue
        first = path.read_text(encoding="utf-8").splitlines()[0]
        atq = batch = job = ""
        for token in first.split():
            if token.startswith("ATQ_EPOCH="):
                atq = token.split("=", 1)[1]
            elif token.startswith("BATCH="):
                batch = token.split("=", 1)[1]
            elif token.startswith("JOB="):
                job = token.split("=", 1)[1]
        rows.append({"name": path.name, "atq_epoch": int(atq or 0), "batch": batch, "job": job})
    rows.sort(key=lambda r: (r["atq_epoch"], r["name"]))
    return rows


def wrap_meta(script_rel: str, umask_octal: str) -> dict:
    path = SCRIPTS / script_rel
    interpreter = "sh"
    if path.is_file():
        first = path.read_text(encoding="utf-8").splitlines()[0].strip()
        if first.startswith("#!"):
            interpreter = first[2:].strip().split("/")[-1] or "sh"
    return {"interpreter": interpreter, "effective_umask": format(int(umask_octal, 8), "04o")}


def reference_run(scenario: str | Path, seed: str, clock_epoch: int) -> dict:
    scenario_dir = Path(scenario) if str(scenario).startswith("/") else FIXTURES / str(scenario)
    scenario_label = scenario_dir.name if str(scenario).startswith("/") else str(scenario)
    conf = json.loads((scenario_dir / "scenario.conf.json").read_text(encoding="utf-8"))
    timezone = conf.get("system_timezone", "UTC")
    leave_pending = set(conf.get("leave_pending", []))

    copy_scenario(scenario_dir)

    timeline: list[dict] = []
    seq = 0
    jobs_run: list[str] = []
    jobs_skipped: list[dict] = []
    mail_log: list[dict] = []
    batch_slots_held: list[str] = []

    def emit(event: str, jkey: str, epoch: int) -> None:
        nonlocal seq
        seq += 1
        timeline.append({"seq": seq, "event": event, "job": jkey, "epoch": epoch})

    def hold_slot(letter: str) -> None:
        if letter not in batch_slots_held:
            batch_slots_held.append(letter)

    def release_slot(letter: str) -> None:
        nonlocal batch_slots_held
        batch_slots_held = [x for x in batch_slots_held if x != letter]

    all_jobs: list[tuple[str, dict]] = []
    for batch in conf.get("batches", []):
        batch_id = batch["batch_id"]
        for job in batch.get("jobs", []):
            all_jobs.append((batch_id, job))

    for batch_id, job in all_jobs:
        job_id = job["job_id"]
        jkey = job_key(batch_id, job_id)
        atq_epoch = int(job["atq_epoch"])
        script_rel = job["script"]
        exit_code = int(job.get("exit_code", 0))
        start_letter = job.get("start_letter", "a")
        umask_octal = job.get("umask", "0022")

        emit("registry_read", jkey, clock_epoch)
        if clock_epoch < atq_epoch:
            jobs_skipped.append({"job": jkey, "reason": "not_due"})
            continue

        seq_val = read_seq()
        letter = allocate_letter(start_letter)
        if not letter:
            jobs_skipped.append({"job": jkey, "reason": "no_slot"})
            continue
        emit("slot_allocate", jkey, clock_epoch)
        hold_slot(letter)

        spool_name = write_spool(letter, seq_val, batch_id, job_id, atq_epoch, script_rel)
        emit("spool_write", jkey, clock_epoch)
        bump_seq_atomic(seq_val)
        emit("seq_bump", jkey, clock_epoch)

        meta = wrap_meta(script_rel, umask_octal)
        record_path = REGISTRY_DIR / f"{batch_id}.{job_id}.record.json"
        record_path.write_text(
            json.dumps({"completed_at": clock_epoch, "dispatch_meta": meta, "flushed": True}, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

        record_path.unlink(missing_ok=True)
        emit("registry_delete", jkey, clock_epoch)
        if exit_code != 0:
            mail_log.append({"job": jkey, "exit_code": exit_code})
            emit("mail_sent", jkey, clock_epoch)

        if jkey not in leave_pending:
            complete_spool(spool_name, letter)
            emit("job_complete", jkey, clock_epoch)
            emit("slot_release", jkey, clock_epoch)
            release_slot(letter)
        else:
            # leave spool pending for atq snapshot
            pass

        jobs_run.append(jkey)

    emit("atq_refresh", "system", clock_epoch)

    registry_final: dict[str, dict] = {}
    for path in sorted(REGISTRY_DIR.glob("*.record.json")):
        name = path.name.replace(".record.json", "", 1)
        bid, jid = name.split(".", 1)
        registry_final[job_key(bid, jid)] = json.loads(path.read_text(encoding="utf-8"))

    seq_final = read_seq()
    return {
        "export_version": 1,
        "scenario": scenario_label,
        "seed": seed,
        "clock_epoch": clock_epoch,
        "timezone": timezone,
        "jobs_run": jobs_run,
        "jobs_skipped": jobs_skipped,
        "timeline": timeline,
        "registry_final": registry_final,
        "mail_log": mail_log,
        "atq_lines": build_atq_lines(),
        "seq_final": seq_final,
        "batch_slots_held": batch_slots_held,
    }
