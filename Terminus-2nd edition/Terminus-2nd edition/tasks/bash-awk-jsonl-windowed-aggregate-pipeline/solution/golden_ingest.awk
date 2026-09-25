#!/usr/bin/env gawk -f
# Golden stage-1 ingest — do not ship in environment image.
# Scans JSONL, first-win dedup, numeric validation, writes accepted staging
# and ingest stats. All file writes are guarded so a bare
# `gawk -f ingest.awk /dev/null` (no -v vars) never fatals on a null redirect.

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

# Returns 1 and sets g_value when value is a valid JSON number or numeric
# string; returns 0 for missing, null, NaN, empty, or non-numeric strings.
function parse_value(s,    pat, m, inner) {
  g_value = 0
  pat = "\"value\"[[:space:]]*:[[:space:]]*\"([^\"]*)\""
  if (match(s, pat, m)) {
    inner = m[1]
    if (inner == "" || inner == "null" || inner == "NaN" || inner == "nan") {
      return 0
    }
    if (inner ~ /^-?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?$/) {
      g_value = inner + 0
      return 1
    }
    return 0
  }
  pat = "\"value\"[[:space:]]*:[[:space:]]*(-?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?)"
  if (match(s, pat, m)) {
    g_value = m[1] + 0
    return 1
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

  if (!parse_value(line)) {
    events_skipped_invalid_value++
    next
  }

  epoch = rfc3339_to_epoch(ts)
  events_accepted++
  footer_sum += g_value

  if (accepted_path != "") {
    printf "{\"epoch\": %d, \"tenant\": \"%s\", \"metric\": \"%s\", \"value\": %s}\n", \
      epoch, tenant, metric, fmt_num(g_value) > accepted_path
  }
}

END {
  if (stats_path != "") {
    printf "{\"lines_read\": %d, \"events_accepted\": %d, \"events_deduped\": %d, \"events_skipped_invalid_value\": %d, \"footer_sum\": %s}\n", \
      lines_read, events_accepted, events_deduped, events_skipped_invalid_value, fmt_num(footer_sum) > stats_path
  }
}
