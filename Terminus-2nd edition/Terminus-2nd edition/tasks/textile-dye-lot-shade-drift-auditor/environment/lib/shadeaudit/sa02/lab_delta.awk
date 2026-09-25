#!/usr/bin/awk -f
# BROKEN baseline: sum of squares without sqrt.
BEGIN { OFMT = "%.6f" }
function cie76(l1,a1,b1,l2,a2,b2) {
  dl = l1 - l2; da = a1 - a2; db = b1 - b2
  return dl*dl + da*da + db*db
}
