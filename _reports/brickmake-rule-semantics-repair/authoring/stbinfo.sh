#!/bin/bash
root=$(ls -d ~/.local/share/uv/tools/snorkelai-stb/lib/python*/site-packages/snorkelai_stb)
f=$(grep -rl "def select_portkey_project_at_login" "$root" | head -1)
echo "$f"
n=$(grep -n "def select_portkey_project_at_login" "$f" | cut -d: -f1)
sed -n "$n,$((n+45))p" "$f"
grep -n "^from\|^import" "$root/auth.py" | head -30
