#!/usr/bin/env bash
set -euo pipefail
ipt_path="$1"
python3 -c "
import json, re, sys
text = open(sys.argv[1]).read()
found = []
for mod in ('mark', 'addrtype'):
    if re.search(rf'-m\s+{mod}\b', text):
        found.append(mod)
print(json.dumps(sorted(found)))
" "$ipt_path"
