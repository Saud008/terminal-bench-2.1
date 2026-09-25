#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

client_list_matches() {
  local ip="$1"
  local clients_json="$2"
  python3 - "$ip" "$clients_json" <<'PY'
import json, sys, ipaddress

ip_s, clients = sys.argv[1], json.loads(sys.argv[2])

def match_one(pat):
    pat = pat.strip()
    if pat.upper().startswith("ALL EXCEPT"):
        rest = pat[len("ALL EXCEPT"):].strip()
        subs = rest.split() if rest else []
        for sub in subs:
            if match_one(sub):
                return False
        return True
    if pat == "ALL":
        return True
    if "/" in pat:
        net = ipaddress.ip_network(pat, strict=False)
        addr = ipaddress.ip_address(ip_s)
        if addr.version != net.version:
            return False
        return addr in net
    return ip_s == pat

for client in clients:
    if match_one(client):
        print("yes")
        raise SystemExit
print("no")
PY
}

ip_matches_pattern() {
  local ip="$1"
  local pattern="$2"
  client_list_matches "$ip" "[\"$pattern\"]"
}
