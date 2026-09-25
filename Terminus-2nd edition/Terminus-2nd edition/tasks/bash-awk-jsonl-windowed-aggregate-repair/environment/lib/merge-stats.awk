#!/usr/bin/env gawk -f
# Legacy stats merge helper — not invoked by agg-run.

BEGIN {
  print "merge-stats: not used by agg-run" > "/dev/stderr"
}

{
  print
}
