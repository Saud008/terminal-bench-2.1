#!/bin/bash
# List running run_k wrappers with their SLUG.
for p in $(pgrep -f 'runk.sh|run_k.sh'); do
	[ "$p" = "$$" ] && continue
	slug=$(tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null | sed -n 's/^SLUG=//p')
	echo "$p slug=${slug:-?} $(tr '\0' ' ' < "/proc/$p/cmdline" | cut -c1-120)"
done
