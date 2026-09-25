#!/usr/bin/env bash
set -euo pipefail
nft_path="$1"
python3 -c "
import json, re, sys
text = open(sys.argv[1]).read()
rows = []
for m in re.finditer(r'chain\s+(\w+)\s*\{[^}]*?policy\s+(\w+);', text, re.I | re.S):
    nc = m.group(1).lower()
    mapping = {'input': 'INPUT', 'forward': 'FORWARD', 'output': 'OUTPUT'}
    chain = mapping.get(nc, nc.upper())
    rows.append({
        'chain': chain,
        'nft_chain': nc,
        'iptables_policy': 'ACCEPT',
        'nft_policy': m.group(2).lower(),
        'hook_priority': 0,
        'precedence_rank': 1,
    })
print(json.dumps(rows))
" "$nft_path"
