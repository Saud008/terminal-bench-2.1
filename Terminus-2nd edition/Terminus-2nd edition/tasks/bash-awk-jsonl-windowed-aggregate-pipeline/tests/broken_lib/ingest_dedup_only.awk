#!/usr/bin/env gawk -f
# Partial ingest fix: first-win dedup only. Numeric validation is still missing
# (non-numeric values are coerced to 0 instead of skipped).

BEGIN {
  OFS = ""
  lines_read = 0
  events_accepted = 0
  events_deduped = 0
  events_skipped_invalid_value = 0
  footer_sum = 0
}

function json_str(s, name,    pat, m) {
  pat = "\"" name "\"[[:space:]]*:[[:space:]]*\"([^\"]*)\""
  if (match(s, pat, m)) {
    return m[1]
  }
  return ""
}

function json_num(s, name,    pat, m) {
  pat = "\"" name "\"[[:space:]]*:[[:space:]]*\"([^\"]*)\""
  if (match(s, pat, m)) {
    return m[1] + 0
  }
  pat = "\"" name "\"[[:space:]]*:[[:space:]]*(-?[0-9]+(\.[0-9]+)?)"
  if (match(s, pat, m)) {
    return m[1] + 0
  }
  return 0
}

function rfc3339_to_epoch(t,    m, spec) {
  if (match(t, /^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})/, m)) {
    spec = m[1] " " m[2] " " m[3] " " m[4] " " m[5] " " m[6]
    return mktime(spec, 1)
  }
  return 0
}

function fmt_num(v,    iv) {
  iv = int(v)
  if (v == iv) {
    return sprintf("%d", iv)
  }
  return sprintf("%.6g", v)
}

{
  line = $0
  sub(/\r$/, "", line)
  if (line ~ /^[[:space:]]*$/) {
    next
  }
  lines_read++

  event_id = json_str(line, "event_id")
  tenant = json_str(line, "tenant")
  metric = json_str(line, "metric")
  ts = json_str(line, "ts")

  if (event_id == "" || tenant == "" || metric == "" || ts == "") {
    events_skipped_invalid_value++
    next
  }

  if (event_id in seen) {
    events_deduped++
    next
  }
  seen[event_id] = 1

  value = json_num(line, "value")
  epoch = rfc3339_to_epoch(ts)
  events_accepted++
  footer_sum += value

  if (accepted_path != "") {
    printf "{\"epoch\": %d, \"tenant\": \"%s\", \"metric\": \"%s\", \"value\": %s}\n", \
      epoch, tenant, metric, fmt_num(value) > accepted_path
  }
}

END {
  if (stats_path != "") {
    printf "{\"lines_read\": %d, \"events_accepted\": %d, \"events_deduped\": %d, \"events_skipped_invalid_value\": %d, \"footer_sum\": %s}\n", \
      lines_read, events_accepted, events_deduped, events_skipped_invalid_value, fmt_num(footer_sum) > stats_path
  }
}
