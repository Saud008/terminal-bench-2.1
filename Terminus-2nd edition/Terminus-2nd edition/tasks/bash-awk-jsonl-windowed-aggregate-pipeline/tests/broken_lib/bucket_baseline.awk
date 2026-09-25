#!/usr/bin/env gawk -f
# Stage 2: tumbling-window rollup from staging ledger.

BEGIN {
  OFS = ""
  window_sec = window_sec + 0
  if (window_sec <= 0) {
    print "window_sec must be positive" > "/dev/stderr"
    exit 1
  }
}

function json_field(line, name,    pat, m) {
  pat = "\"" name "\"[[:space:]]*:[[:space:]]*\"([^\"]*)\""
  if (match(line, pat, m)) {
    return m[1]
  }
  pat = "\"" name "\"[[:space:]]*:[[:space:]]*(-?[0-9]+(\.[0-9]+)?)"
  if (match(line, pat, m)) {
    return m[1]
  }
  return ""
}

function fmt_num(v,    iv) {
  iv = int(v)
  if (v == iv) {
    return sprintf("%d", iv)
  }
  return sprintf("%.6g", v)
}

function emit_rollup(    keys, n, i, key, parts, b, tenant, metric) {
  delete keys
  n = 0
  for (key in sum_v) {
    keys[++n] = key
  }
  asort(keys)
  for (i = 1; i <= n; i++) {
    key = keys[i]
    split(key, parts, SUBSEP)
    b = parts[1] + 0
    tenant = tenant_v[key]
    metric = metric_v[key]
    printf "{\"bucket\": %d, \"tenant\": \"%s\", \"metric\": \"%s\", \"sum\": %s, \"count\": %d, \"min\": %s, \"max\": %s}\n", \
      b, tenant, metric, fmt_num(sum_v[key]), count_v[key], fmt_num(min_v[key]), fmt_num(max_v[key]) > rollup_path
  }
}

{
  line = $0
  sub(/\r$/, "", line)
  if (line == "") {
    next
  }

  epoch = json_field(line, "epoch") + 0
  tenant = json_field(line, "tenant")
  metric = json_field(line, "metric")
  value = json_field(line, "value") + 0

  bucket = int(epoch / window_sec) * window_sec + 1
  catkey = tenant metric
  key = bucket SUBSEP catkey

  if (!(key in count_v)) {
    sum_v[key] = value
    count_v[key] = 1
    min_v[key] = value
    max_v[key] = value
    tenant_v[key] = tenant
    metric_v[key] = metric
  } else {
    sum_v[key] += value
    count_v[key]++
    if (value < min_v[key]) {
      min_v[key] = value
    }
    if (value > max_v[key]) {
      max_v[key] = value
    }
    tenant_v[key] = tenant
    metric_v[key] = metric
  }
}

END {
  emit_rollup()
}
