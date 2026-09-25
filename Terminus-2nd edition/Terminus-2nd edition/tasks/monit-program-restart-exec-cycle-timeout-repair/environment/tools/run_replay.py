#!/usr/bin/env python3
"""Fixed replay driver — calls /app/lib policy hooks via bash."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

LIB = Path("/app/lib")
APP = Path("/app")


def _bash_hook(script: str, fn: str, *args: str) -> str:
    arglist = " ".join(f'"{a}"' for a in args)
    cmd = f'source "{LIB}/{script}"; {fn} {arglist}'
    proc = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{fn} failed: {proc.stderr}")
    return proc.stdout.strip()


def replay(config: dict[str, Any], scenario: dict[str, Any], scenario_bytes: bytes) -> dict[str, Any]:
    _bash_hook("cycle_counter.sh", "monit_cycle_init")
    stop_started: int | None = None
    stop_timeout = int(config["stop_timeout_sec"])
    start_delay_cfg = int(config["start_delay_sec"])
    restart_limit = int(config["restart_limit"])
    pidfile = str(config.get("pidfile", f"/app/work/{config['program']}.pid"))
    idfile = str(config.get("idfile", f"/app/state/monit-{config['program']}.id"))
    outcomes = list(scenario.get("start_outcomes", []))
    outcome_idx = 0
    unclean_pending = False
    stop_ok = True
    notify_bad = False
    pid_stale = False
    final_state = "init"
    timeline: list[dict[str, Any]] = []
    boot_onreboot_pending = False

    for ev in scenario["events"]:
        kind = ev["kind"]
        t = int(ev["t"])

        if kind == "boot":
            boot_onreboot_pending = bool(ev.get("onreboot", False))
            delay = int(
                _bash_hook(
                    "delay_precedence.sh",
                    "monit_effective_start_delay",
                    "1" if boot_onreboot_pending else "0",
                    str(start_delay_cfg),
                )
            )
            timeline.append({"t": t, "step": "boot", "delay": delay})
            if delay > 0:
                timeline.append({"t": t + delay, "step": "start_exec", "outcome": "pending"})
                t_start = t + delay
            else:
                t_start = t
            outcome = outcomes[outcome_idx] if outcome_idx < len(outcomes) else "ok"
            outcome_idx += 1
            stale_flag = _bash_hook("pidfile.sh", "monit_prepare_pidfile", pidfile, "1" if unclean_pending else "0")
            if stale_flag == "1":
                pid_stale = True
            unclean_pending = False
            if outcome == "ok":
                _bash_hook("pidfile.sh", "monit_write_pidfile", pidfile, f"pid-{t_start}")
                cycles = int(_bash_hook("cycle_counter.sh", "monit_cycle_bump", "running"))
                _bash_hook("notify.sh", "monit_record_transition", idfile, "running", str(t_start))
                final_state = "running"
                timeline.append({"t": t_start, "step": "running", "cycles": cycles})
            else:
                _bash_hook("cycle_counter.sh", "monit_cycle_bump", "fail")
                _bash_hook("notify.sh", "monit_record_transition", idfile, "failed", str(t_start))
                final_state = "failed"
                timeline.append({"t": t_start, "step": "start_failed"})
            boot_onreboot_pending = False

        elif kind == "unclean_kill":
            unclean_pending = True
            _bash_hook("pidfile.sh", "monit_write_pidfile", pidfile, "dead-token")
            timeline.append({"t": t, "step": "unclean_kill"})
            final_state = "not_running"

        elif kind == "stop_begin":
            stop_started = t
            timeline.append({"t": t, "step": "stop_begin"})
            final_state = "stopping"

        elif kind == "restart":
            allowed = _bash_hook(
                "timeout_driver.sh",
                "monit_can_restart_now",
                str(stop_started if stop_started is not None else "none"),
                str(t),
                str(stop_timeout),
            )
            if allowed != "1":
                exec_t = (stop_started or 0) + stop_timeout
                timeline.append({"t": t, "step": "restart_deferred", "until": exec_t})
                t = exec_t
                stop_ok = False
            else:
                if stop_started is not None and t < stop_started + stop_timeout:
                    stop_ok = False
                timeline.append({"t": t, "step": "restart_exec"})
            stop_started = None
            delay = int(
                _bash_hook(
                    "delay_precedence.sh",
                    "monit_effective_start_delay",
                    "0",
                    str(start_delay_cfg),
                )
            )
            if delay > 0:
                timeline.append({"t": t + delay, "step": "start_delay_wait", "delay": delay})
                t = t + delay
            cycles_before = int(_bash_hook("cycle_counter.sh", "monit_cycle_read"))
            if cycles_before >= restart_limit:
                final_state = "cycle_exhausted"
                timeline.append({"t": t, "step": "cycle_exhausted"})
                break
            outcome = outcomes[outcome_idx] if outcome_idx < len(outcomes) else "ok"
            outcome_idx += 1
            stale_flag = _bash_hook("pidfile.sh", "monit_prepare_pidfile", pidfile, "1" if unclean_pending else "0")
            if stale_flag == "1":
                pid_stale = True
            unclean_pending = False
            if outcome == "ok":
                _bash_hook("pidfile.sh", "monit_write_pidfile", pidfile, f"pid-{t}")
                cycles = int(_bash_hook("cycle_counter.sh", "monit_cycle_bump", "running"))
                _bash_hook("notify.sh", "monit_record_transition", idfile, "running", str(t))
                final_state = "running"
                timeline.append({"t": t, "step": "running", "cycles": cycles})
            else:
                _bash_hook("cycle_counter.sh", "monit_cycle_bump", "fail")
                _bash_hook("notify.sh", "monit_record_transition", idfile, "failed", str(t))
                final_state = "failed"
                timeline.append({"t": t, "step": "start_failed"})

    order_marker = Path(str(idfile) + ".order")
    if order_marker.is_file() and order_marker.read_text(encoding="utf-8").strip() == "notify_first":
        notify_bad = True

    cycles_used = int(_bash_hook("cycle_counter.sh", "monit_cycle_read"))
    snap_path = APP / "state" / "cycle-snapshot.json"
    snap_sha = None
    if snap_path.is_file():
        snap_sha = json.loads(snap_path.read_text(encoding="utf-8")).get("snapshot_sha256")
    if not snap_sha:
        snap_sha = hashlib.sha256(scenario_bytes).hexdigest()

    return {
        "program": config["program"],
        "restart_cycles_used": cycles_used,
        "stop_timeout_respected": stop_ok,
        "notify_before_idfile": notify_bad,
        "pidfile_stale_at_start": pid_stale,
        "final_state": final_state,
        "timeline": timeline,
        "snapshot_sha256": snap_sha,
    }


def main() -> None:
    config_path = Path(sys.argv[1])
    scenario_path = Path(sys.argv[2])
    export_path = Path(sys.argv[3])
    raw = scenario_path.read_bytes()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    scenario = json.loads(raw.decode("utf-8"))
    report = replay(config, scenario, raw)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
