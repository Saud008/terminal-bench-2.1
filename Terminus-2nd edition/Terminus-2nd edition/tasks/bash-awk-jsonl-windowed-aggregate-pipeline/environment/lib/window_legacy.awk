#!/usr/bin/env gawk -f
# Legacy windowing prototype — NOT invoked by agg-run. Kept for reference only.
# Do not treat as authoritative; see /app/lib/bucket.awk for the real stage 2.

BEGIN {
  print "window_legacy: not used by agg-run" > "/dev/stderr"
}

{
  print
}
