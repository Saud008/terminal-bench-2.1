#!/usr/bin/env gawk -f
# Legacy prefilter prototype — NOT invoked by agg-run. Kept for reference only.
# Do not treat as authoritative; ingest happens in /app/lib/ingest.awk.

BEGIN {
  print "prefilter: not used by agg-run" > "/dev/stderr"
}

{
  print
}
