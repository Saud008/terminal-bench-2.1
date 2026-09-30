#!/bin/sh
# Smoke tests: smoke/run.sh path/to/hopcfg
bin=${1:-./hopcfg}
here=$(cd "$(dirname "$0")" && pwd)
fail=0
for dir in "$here"/cases/*/; do
	name=$(basename "$dir")
	# shellcheck disable=SC2046
	out=$("$bin" -F "${dir}config" $(cat "${dir}args") 2>&1)
	if [ "$out" = "$(cat "${dir}expected")" ]; then
		echo "ok   $name"
	else
		echo "FAIL $name"
		fail=1
	fi
done
for conf in fleet.conf workstation.conf ci-runner.conf; do
	if "$bin" -F "$here/../examples/$conf" example-host >/dev/null; then
		echo "ok   examples/$conf"
	else
		echo "FAIL examples/$conf"
		fail=1
	fi
done
exit $fail
