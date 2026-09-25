"""Independent Monit program restart FSM reference for monitctl replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def can_restart_now(stop_started: int | None, current_t: int, stop_timeout: int) -> bool:
    if stop_started is None:
        return True
    return current_t >= stop_started + stop_timeout


def effective_start_delay(onreboot_boot: bool, start_delay: int) -> int:
    if onreboot_boot:
        return 0
    return start_delay


def prepare_pidfile(pidfile: Path, unclean: bool) -> bool:
    """Return True if pidfile would still be stale at start."""
    if unclean and pidfile.is_file():
        return True
    return False


def clear_pidfile_if_unclean(pidfile: Path, unclean: bool) -> bool:
    """Return True if stale flag after prepare (correct impl clears file)."""
    stale = prepare_pidfile(pidfile, unclean)
    if unclean and pidfile.is_file():
        pidfile.unlink()
        return False
    return stale


def record_transition(idfile: Path, notify_log: Path, transition: str, t: int) -> bool:
    """Return notify_before_idfile violation flag for this transition."""
    idfile.parent.mkdir(parents=True, exist_ok=True)
    idfile.write_text(f"state={transition} t={t}\n", encoding="utf-8")
    order = idfile.with_suffix(idfile.suffix + ".order")
    order.write_text("idfile_first\n", encoding="utf-8")
    with notify_log.open("a", encoding="utf-8") as fh:
        fh.write(f"{transition} notify t={t}\n")
    return False


def replay_reference(
    config: dict[str, Any],
    scenario: dict[str, Any],
    scenario_bytes: bytes,
    work_root: Path | None = None,
    snapshot_sha: str | None = None,
) -> dict[str, Any]:
    work = work_root or Path("/app/work")
    state = Path("/app/state")
    work.mkdir(parents=True, exist_ok=True)
    state.mkdir(parents=True, exist_ok=True)

    stop_timeout = int(config["stop_timeout_sec"])
    start_delay_cfg = int(config["start_delay_sec"])
    restart_limit = int(config["restart_limit"])
    pidfile = Path(config.get("pidfile", work / f"{config['program']}.pid"))
    idfile = Path(config.get("idfile", state / f"monit-{config['program']}.id"))
    notify_log = state / "notify.log"
    notify_log.write_text("", encoding="utf-8")

    outcomes = list(scenario.get("start_outcomes", []))
    outcome_idx = 0
    cycles = 0
    stop_started: int | None = None
    stop_ok = True
    notify_bad = False
    pid_stale = False
    unclean_pending = False
    final_state = "init"
    timeline: list[dict[str, Any]] = []

    for ev in scenario["events"]:
        kind = ev["kind"]
        t = int(ev["t"])

        if kind == "boot":
            delay = effective_start_delay(bool(ev.get("onreboot", False)), start_delay_cfg)
            timeline.append({"t": t, "step": "boot", "delay": delay})
            t_start = t + delay if delay > 0 else t
            outcome = outcomes[outcome_idx] if outcome_idx < len(outcomes) else "ok"
            outcome_idx += 1
            stale = clear_pidfile_if_unclean(pidfile, unclean_pending)
            if stale:
                pid_stale = True
            unclean_pending = False
            if outcome == "ok":
                pidfile.write_text(f"pid-{t_start}\n", encoding="utf-8")
                cycles += 1
                if record_transition(idfile, notify_log, "running", t_start):
                    notify_bad = True
                final_state = "running"
                timeline.append({"t": t_start, "step": "running", "cycles": cycles})
            else:
                if record_transition(idfile, notify_log, "failed", t_start):
                    notify_bad = True
                final_state = "failed"
                timeline.append({"t": t_start, "step": "start_failed"})

        elif kind == "unclean_kill":
            unclean_pending = True
            pidfile.write_text("dead-token\n", encoding="utf-8")
            timeline.append({"t": t, "step": "unclean_kill"})
            final_state = "not_running"

        elif kind == "stop_begin":
            stop_started = t
            timeline.append({"t": t, "step": "stop_begin"})
            final_state = "stopping"

        elif kind == "restart":
            if not can_restart_now(stop_started, t, stop_timeout):
                exec_t = (stop_started or 0) + stop_timeout
                timeline.append({"t": t, "step": "restart_deferred", "until": exec_t})
                t = exec_t
                stop_ok = False
            else:
                if stop_started is not None and t < stop_started + stop_timeout:
                    stop_ok = False
                timeline.append({"t": t, "step": "restart_exec"})
            stop_started = None
            delay = effective_start_delay(False, start_delay_cfg)
            if delay > 0:
                timeline.append({"t": t + delay, "step": "start_delay_wait", "delay": delay})
                t = t + delay
            if cycles >= restart_limit:
                final_state = "cycle_exhausted"
                timeline.append({"t": t, "step": "cycle_exhausted"})
                break
            outcome = outcomes[outcome_idx] if outcome_idx < len(outcomes) else "ok"
            outcome_idx += 1
            stale = clear_pidfile_if_unclean(pidfile, unclean_pending)
            if stale:
                pid_stale = True
            unclean_pending = False
            if outcome == "ok":
                pidfile.write_text(f"pid-{t}\n", encoding="utf-8")
                cycles += 1
                if record_transition(idfile, notify_log, "running", t):
                    notify_bad = True
                final_state = "running"
                timeline.append({"t": t, "step": "running", "cycles": cycles})
            else:
                if record_transition(idfile, notify_log, "failed", t):
                    notify_bad = True
                final_state = "failed"
                timeline.append({"t": t, "step": "start_failed"})

    if not snapshot_sha:
        snapshot_sha = hashlib.sha256(scenario_bytes).hexdigest()

    return {
        "program": config["program"],
        "restart_cycles_used": cycles,
        "stop_timeout_respected": stop_ok,
        "notify_before_idfile": notify_bad,
        "pidfile_stale_at_start": pid_stale,
        "final_state": final_state,
        "timeline": timeline,
        "snapshot_sha256": snapshot_sha,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
