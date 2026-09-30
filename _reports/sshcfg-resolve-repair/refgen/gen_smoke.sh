#!/bin/bash
# Write t/cases/*/expected from real ssh -G; confirm good and bad builds agree.
set -u
cd /app/t/cases
for d in */; do
	d=${d%/}
	args=$(cat "$d/args")
	# shellcheck disable=SC2086
	env -i PATH=/usr/bin:/bin HOME=/root USER=root LC_ALL=C \
		ssh -G -F "/app/t/cases/$d/config" $args 2>&1 | python3 -c '
import sys
sys.path.insert(0, "/w")
import harness
sys.stdout.write(harness.filter_ssh(sys.stdin.read()))' > "/out/$d/expected"
	for b in /g/hopcfg /b/hopcfg; do
		# shellcheck disable=SC2086
		if [ "$($b -F "/app/t/cases/$d/config" $args 2>&1)" = "$(cat "/out/$d/expected")" ]; then
			echo "$d $b ok"
		else
			echo "$d $b DIFF"
		fi
	done
done
