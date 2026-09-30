#!/bin/bash
# Show where API keys come from, masked (last 4 chars only).
mask() { local v=$1; [ -n "$v" ] && echo "len=${#v} ...${v: -4}" || echo "(unset)"; }
echo "== ~/.config/stb/config.ini (masked)"
sed -E 's/^([^=]+=\s*).*(.{4})$/\1***\2/' ~/.config/stb/config.ini
echo "== env in login shell"
for v in OPENAI_API_KEY PORTKEY_API_KEY OPENAI_BASE_URL OPENAI_API_BASE STB_API_KEY; do
	echo "$v: $(mask "${!v}")"
done
echo "== exports in shell rc files"
grep -nE 'export +(OPENAI|PORTKEY|STB)[A-Z_]*=' ~/.bashrc ~/.profile ~/.bash_profile 2>/dev/null \
	| sed -E 's/=.*(.{4})["'"'"']?$/=***\1/'
