#!/usr/bin/env bash
# Partial fix: real IPv6 membership in client_list_matches; legacy ip_matches_pattern still broken.

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
  python3 - "$ip" "$pattern" <<'PY'
import ipaddress, sys

ip_s, pat = sys.argv[1], sys.argv[2]
pat = pat.strip()
if pat.upper().startswith("ALL EXCEPT"):
    rest = pat[len("ALL EXCEPT"):].strip()
    subs = rest.split() if rest else []
    for sub in subs:
        if ip_matches(sub):
            print("yes")
            raise SystemExit
    print("no")
    raise SystemExit

if pat == "ALL":
    print("yes")
    raise SystemExit

def ip_matches(p):
    if "/" in p:
        net = ipaddress.ip_network(p, strict=False)
        addr = ipaddress.ip_address(ip_s)
        if addr.version != net.version:
            return False
        if addr.version == 6:
            prefix = net.prefixlen
            n_chars = max(1, prefix // 4)
            return ip_s.replace(":", "")[:n_chars] == str(net.network_address).replace(":", "")[:n_chars]
        return addr in net
    return ip_s == p

print("yes" if ip_matches(pat) else "no")
PY
}
