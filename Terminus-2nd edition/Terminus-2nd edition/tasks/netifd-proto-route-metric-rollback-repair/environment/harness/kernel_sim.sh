#!/usr/bin/env bash
# Thin wrapper around harness/state.py for Bash modules.

harness_reset() {
  python3 -c "import sys; sys.path.insert(0,'/app/harness'); import state; state.reset()"
}

harness_py() {
  python3 - "$@" <<'PY'
import json
import sys
sys.path.insert(0, "/app/harness")
import state

cmd = sys.argv[1]
args = sys.argv[2:]
if cmd == "assign_metric":
    iface, cfg, bonus = args
    print(state.assign_metric(iface, int(cfg), int(bonus)))
elif cmd == "get_assigned_metric":
    iface, fallback = args
    print(state.get_assigned_metric(iface, int(fallback)))
elif cmd == "route_add":
    dst, via, dev, metric = args
    state.route_add(dst, via, dev, int(metric))
elif cmd == "route_del_default":
    state.route_del_default(args[0])
elif cmd == "link_up":
    state.link_up(args[0])
elif cmd == "link_down":
    state.link_down(args[0])
elif cmd == "link_down_ack":
    state.link_down_ack(args[0])
elif cmd == "link_down_acknowledged":
    print("yes" if state.link_down_acknowledged(args[0]) else "no")
elif cmd == "addr_add":
    dev, family, addr, dedupe = args[0], args[1], args[2], args[3] == "1"
    state.addr_add(dev, family, addr, dedupe)
elif cmd == "pd_acquire":
    state.pd_acquire(args[0], args[1], args[2])
elif cmd == "pd_release_iface":
    state.pd_release_iface(args[0])
elif cmd == "rules_set":
    state.rules_set(json.loads(args[0]))
elif cmd == "rules_commit":
    state.rules_commit()
elif cmd == "rules_committed":
    print("yes" if state.rules_committed() else "no")
elif cmd == "reload_prepare":
    state.reload_prepare(args[0])
elif cmd == "export_payload":
    scenario, iface = args
    print(json.dumps(state.export_payload(scenario, iface)))
else:
    raise SystemExit(f"unknown harness command: {cmd}")
PY
}
