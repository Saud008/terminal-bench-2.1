#!/bin/bash
# scan_pii.sh: list local-path / stb leaks under trajectories/ and oracle-nop-evidence/ (check 89).
S=brickmake-rule-semantics-repair
cd "$S"
grep -rnoE '/mnt/c/[^"]{0,60}|/Users/[^"]{0,40}|/home/saud[^"]{0,40}|/private/tmp[^"]{0,30}|file:///mnt[^"]{0,40}' trajectories oracle-nop-evidence \
  | awk -F: '{print $1": "$3}' | sort | uniq -c | sort -rn | head -40
echo "--- word stb"
grep -rnwc 'stb' trajectories oracle-nop-evidence | grep -v ':0$' | head
