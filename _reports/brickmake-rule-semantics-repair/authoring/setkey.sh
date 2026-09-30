#!/bin/bash
# setkey.sh: load the stb AI key from C:\Users\masau\stbkey.txt without printing it
# (same steps as `stb keys set`, whose hidden prompt cannot read a pipe).
PY=$(ls ~/.local/share/uv/tools/snorkelai-stb/bin/python | head -1)
"$PY" - <<'EOF'
from snorkelai_stb.auth import validate_portkey_key, set_portkey_config, clear_stored_portkey_project_id
key = open("/mnt/c/Users/masau/stbkey.txt", encoding="utf-8-sig").read().strip()
print("key length:", len(key))
validate_portkey_key(key)
set_portkey_config(key)
clear_stored_portkey_project_id()
print("saved")
EOF
echo "--- verify"
stb keys verify 2>&1 | tail -3
