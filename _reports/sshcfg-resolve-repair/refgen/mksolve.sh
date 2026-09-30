#!/bin/bash
# Build solution/solve.sh: one patch heredoc per file that differs.
set -eu
out=/out/solve.sh
{
	printf '#!/usr/bin/env bash\nset -euo pipefail\n\ncd /app\n'
	for f in readconf.c matchcfg.c main.c convtime.c strlist.c jump.c options.c dump.c; do
		printf '\npatch -p1 <<'"'"'EOF'"'"'\n'
		diff -u --label "a/src/$f" --label "b/src/$f" "/bad/src/$f" "/good/src/$f" || true
		printf 'EOF\n'
	done
	printf '\nmake clean\nmake\nmake check\n'
} > "$out"
for f in /bad/src/*; do
	b=$(basename "$f")
	case " readconf.c matchcfg.c main.c convtime.c strlist.c jump.c options.c dump.c " in
	*" $b "*) ;;
	*) cmp -s "$f" "/good/src/$b" || echo "UNLISTED DIFF $b" ;;
	esac
done
