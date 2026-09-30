#!/bin/bash
# login.sh [project-number]: the steps of `stb login --env prod` with the Snorkel API key read from
# C:\Users\masau\stbkey.txt (never printed). AI credentials are left to run_k.sh's own single refresh.
PY=~/.local/share/uv/tools/snorkelai-stb/bin/python
"$PY" - "${1:-}" <<'EOF'
import os, sys
from urllib.error import HTTPError
from snorkelai_stb.config import GlobalConfig
from snorkelai_stb.constants import Env
from snorkelai_stb.utils import get_current_user_info
from snorkelai_stb.portkey_utils import get_portkey_api_key_options, set_stored_portkey_project_id

key = open("/mnt/c/Users/masau/stbkey.txt", encoding="utf-8-sig").read().strip()
GlobalConfig.set("auth", "env", Env("prod").value)
os.environ["SNORKEL_API_KEY"] = key
try:
    get_current_user_info()
except HTTPError as e:
    sys.exit(f"API key rejected by prod: HTTP {e.code}")
GlobalConfig.set("auth", "api_key", key)
print("API key valid, saved (env prod)")
projects = get_portkey_api_key_options()
if not projects:
    sys.exit("no eligible projects for AI credentials")
for i, p in enumerate(projects, 1):
    print(f"  {i}. {p['name']}")
choice = sys.argv[1]
if len(projects) == 1:
    choice = "1"
if not choice:
    sys.exit("several projects: rerun with the project number")
p = projects[int(choice) - 1]
set_stored_portkey_project_id(p["project_id"])
print("project saved:", p["name"])
EOF
