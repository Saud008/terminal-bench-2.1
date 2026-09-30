#!/bin/bash
# Progress of the newest run_k job for this task.
cd ~/tbruns || exit 1
d=$(ls -td sshcfg-resolve-repair-k*-*/ 2>/dev/null | head -1)
echo "$d"
for t in "$d"*/; do
	[ -d "$t/agent" ] || continue
	calls=$(wc -l < "$t/agent/api-calls.jsonl" 2>/dev/null || echo 0)
	echo "$(basename "$t") api_calls=$calls reward=$(cat "$t/verifier/reward.txt" 2>/dev/null || echo -)"
done
