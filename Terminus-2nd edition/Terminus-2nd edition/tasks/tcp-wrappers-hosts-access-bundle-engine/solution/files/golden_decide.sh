#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=parse.sh
source "$(dirname "${BASH_SOURCE[0]}")/parse.sh"
# shellcheck source=aliases.sh
source "$(dirname "${BASH_SOURCE[0]}")/aliases.sh"
# shellcheck source=cidr.sh
source "$(dirname "${BASH_SOURCE[0]}")/cidr.sh"
# shellcheck source=publish.sh
source "$(dirname "${BASH_SOURCE[0]}")/publish.sh"

decide_access() {
  local root="$1"
  local daemon="$2"
  local ip="$3"
  local export_path="$4"
  local alias_json manifest name rules_json payload fp
  alias_json="$(load_alias_map "$root")"
  manifest="$(read_manifest "$root")"
  name="$(python3 - "$manifest" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["name"])
PY
)"
  rules_json="$(load_cached_rules "$root" "$name" || true)"
  if [[ -z "$rules_json" ]]; then
    rules_json="$(load_bundle_rules "$root")"
    fp="$(bundle_fingerprint "$root")"
    merged_payload="$(python3 - "$name" "$rules_json" <<'PY'
import json, sys
name, rules = sys.argv[1], json.loads(sys.argv[2])
allow = [r for r in rules if r["side"] == "allow"]
deny = [r for r in rules if r["side"] == "deny"]
merged = allow + deny
for idx, rule in enumerate(merged):
    rule["index"] = idx
print(json.dumps({
    "bundle": name,
    "rules": merged,
    "stats": {
        "allow_rules": len(allow),
        "deny_rules": len(deny),
        "total_rules": len(merged),
    },
}, indent=2))
PY
)"
    write_merge_staging "$name" "$merged_payload"
    publish_from_staging "$name" "$fp" "" "$merged_payload"
    rules_json="$(python3 - "$merged_payload" <<'PY'
import json, sys
print(json.dumps(json.loads(sys.argv[1])["rules"]))
PY
)"
  fi
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


def canonical(query: str) -> str:
    proc = bash_run(
        'source "${HOSTSCTL_LIB}/common.sh"; '
        'source "${HOSTSCTL_LIB}/aliases.sh"; '
        'canonical_daemon "$1" "$2"',
        alias_json,
        query,
    )
    return proc.stdout.strip()


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
                "daemon": canon,
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


canon = canonical(daemon)
for rule in merged:
    if rule["side"] != "allow":
        continue
    if daemon_match(rule["daemons"], daemon) and client_match(ip, rule["clients"]):
        finish("allow", rule["index"], "allow", "first_match")
for rule in merged:
    if rule["side"] != "deny":
        continue
    if daemon_match(rule["daemons"], daemon) and client_match(ip, rule["clients"]):
        finish("deny", rule["index"], "deny", "first_match")
finish("deny", -1, "", "default_deny")
PY
)"
  json_write "$export_path" "$payload"
}
