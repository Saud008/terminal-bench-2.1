#!/usr/bin/env bash
# Stable sort helper for export findings — invoked from map_engine export path.
set -euo pipefail
python3 -c "import json,sys; d=json.load(sys.stdin); d['findings']=sorted(d.get('findings',[]), key=lambda f:(f.get('category',''),f.get('chain',''),f.get('iptables_ordinal') or 0)); json.dump(d,sys.stdout,indent=2)"
