#!/usr/bin/env bash
# Partial fix: correct allow-then-deny order but skips ALL-only deny rules.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=parse.sh
source "$(dirname "${BASH_SOURCE[0]}")/parse.sh"
# shellcheck source=aliases.sh
source "$(dirname "${BASH_SOURCE[0]}")/aliases.sh"
# shellcheck source=cidr.sh
source "$(dirname "${BASH_SOURCE[0]}")/cidr.sh"

decide_access() {
  local root="$1"
  local daemon="$2"
  local ip="$3"
  local export_path="$4"
  local alias_json manifest name rules_json payload
  alias_json="$(load_alias_map "$root")"
  manifest="$(read_manifest "$root")"
  name="$(python3 - "$manifest" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["name"])
PY
)"
  rules_json="$(load_bundle_rules "$root")"
  payload="$(HOSTSCTL_LIB="${HOSTSCTL_LIB}" python3 - "$name" "$daemon" "$ip" "$alias_json" "$rules_json" <<'PY'
import json
import os
import subprocess
import sys

name, daemon, ip, alias_json, rules_json = sys.argv[1:6]
lib = os.environ["HOSTSCTL_LIB"]
rules = json.loads(rules_json)
allow = [r for r in rules if r["side"] == "allow"]
deny = [r for r in rules if r["side"] == "deny"]
merged = allow + deny
for idx, rule in enumerate(merged):
    rule["index"] = idx


def bash_run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", script, "_", *args],
        env={**os.environ, "HOSTSCTL_LIB": lib},
        capture_output=True,
        text=True,
        check=False,
    )


def daemon_match(rule_daemons: list[str], query: str) -> bool:
    for token in rule_daemons:
        proc = bash_run(
            'source "${HOSTSCTL_LIB}/common.sh"; '
            'source "${HOSTSCTL_LIB}/aliases.sh"; '
            'daemon_rule_match "$1" "$2" "$3"',
            alias_json,
            query,
            token,
        )
        if proc.returncode == 0:
            return True
    return False


def client_match(ip_s: str, clients: list[str]) -> bool:
    proc = bash_run(
        'source "${HOSTSCTL_LIB}/common.sh"; '
        'source "${HOSTSCTL_LIB}/cidr.sh"; '
        'client_list_matches "$1" "$2"',
        ip_s,
        json.dumps(clients),
    )
    return proc.stdout.strip() == "yes"


def finish(decision: str, idx: int, side: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "bundle": name,
                "daemon": daemon,
                "ip": ip,
                "decision": decision,
                "matched_rule_index": idx,
                "matched_side": side,
                "reason": reason,
            },
            indent=2,
        )
    )
    raise SystemExit


for rule in merged:
    if rule["side"] != "allow":
        continue
    if daemon_match(rule["daemons"], daemon) and client_match(ip, rule["clients"]):
        finish("allow", rule["index"], "allow", "first_match")
for rule in merged:
    if rule["side"] != "deny":
        continue
    if rule["daemons"] == ["ALL"]:
        continue
    if daemon_match(rule["daemons"], daemon) and client_match(ip, rule["clients"]):
        finish("deny", rule["index"], "deny", "first_match")
finish("deny", -1, "", "default_deny")
PY
)"
  json_write "$export_path" "$payload"
}
