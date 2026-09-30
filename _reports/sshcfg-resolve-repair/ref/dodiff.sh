#!/bin/bash
cd "$(dirname "$0")"
for f in readconf.c ssh.c misc.c match.c; do
  echo "=== $f"
  diff "$f" "deb/$f"
done > debdiff.txt
wc -l debdiff.txt
