#!/usr/bin/env gawk -f
# Golden stage-3 export — do not ship in environment image.

BEGIN {
  OFS = ""
  window_sec = window_sec + 0
  run_seq = run_seq + 0
  load_stats()
  validate_manifest()
}

function load_stats(    line) {
  lines_read = 0
  events_accepted = 0
  events_deduped = 0
  events_skipped_invalid_value = 0
  footer_sum = 0
  if ((getline line < stats_path) <= 0) {
    close(stats_path)
    return
  }
  close(stats_path)
  if (match(line, /"lines_read"[[:space:]]*:[[:space:]]*([0-9]+)/, m)) {
    lines_read = m[1] + 0
  }
  if (match(line, /"events_accepted"[[:space:]]*:[[:space:]]*([0-9]+)/, m)) {
    events_accepted = m[1] + 0
  }
  if (match(line, /"events_deduped"[[:space:]]*:[[:space:]]*([0-9]+)/, m)) {
    events_deduped = m[1] + 0
  }
  if (match(line, /"events_skipped_invalid_value"[[:space:]]*:[[:space:]]*([0-9]+)/, m)) {
    events_skipped_invalid_value = m[1] + 0
  }
  if (match(line, /"footer_sum"[[:space:]]*:[[:space:]]*(-?[0-9]+(\.[0-9]+)?)/, m)) {
    footer_sum = m[1] + 0
  }
}

function validate_manifest(    line, manifest_events, manifest_sha, cmd, actual_sha) {
  if ((getline line < manifest_path) <= 0) {
    print "export: missing ledger manifest" > "/dev/stderr"
    exit 1
  }
  close(manifest_path)
  manifest_events = 0
  manifest_sha = ""
  if (match(line, /"events_accepted"[[:space:]]*:[[:space:]]*([0-9]+)/, m)) {
    manifest_events = m[1] + 0
  }
  if (match(line, /"accepted_sha256"[[:space:]]*:[[:space:]]*"([^"]+)"/, m)) {
    manifest_sha = m[1]
  }
  if (manifest_events != events_accepted) {
    print "export: manifest events_accepted mismatch" > "/dev/stderr"
    exit 1
  }
  cmd = "sha256sum " accepted_path " 2>/dev/null"
  cmd | getline line
  close(cmd)
  if (match(line, /^([a-f0-9]+)/, m)) {
    actual_sha = m[1]
  }
  if (manifest_sha != actual_sha) {
    print "export: manifest sha256 mismatch" > "/dev/stderr"
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

function epoch_to_rfc3339(sec,    s) {
  s = strftime("%Y-%m-%dT%H:%M:%SZ", sec, 1)
  return s
}

function fmt_num(v,    iv) {
  iv = int(v)
  if (v == iv) {
    return sprintf("%d", iv)
  }
  return sprintf("%.6g", v)
}

function emit_report(    buckets, b, key, parts, tenant, metric, wi, si, first, n, sk) {
  delete buckets
  for (key in sum_v) {
    split(key, parts, SUBSEP)
    b = parts[1]
    buckets[b] = 1
  }

  n = 0
  for (b in buckets) {
    bucket_list[++n] = b + 0
  }
  asort(bucket_list)

  print "{" > output
  print "  \"agg_version\": 1," > output
  printf "  \"window_sec\": %d,\n", window_sec > output
  print "  \"stats\": {" > output
  printf "    \"lines_read\": %d,\n", lines_read > output
  printf "    \"events_accepted\": %d,\n", events_accepted > output
  printf "    \"events_deduped\": %d,\n", events_deduped > output
  printf "    \"events_skipped_invalid_value\": %d\n", events_skipped_invalid_value > output
  print "  }," > output
  print "  \"windows\": [" > output

  first = 1
  for (wi = 1; wi <= n; wi++) {
    b = bucket_list[wi]
    delete skeys
    for (key in sum_v) {
      split(key, parts, SUBSEP)
      if (parts[1] + 0 != b) {
        continue
      }
      sk = parts[2] SUBSEP parts[3]
      skeys[sk] = parts[2] SUBSEP parts[3]
    }
    delete series_order
    sc = 0
    for (sk in skeys) {
      split(skeys[sk], parts, SUBSEP)
      series_order[++sc] = parts[1] SUBSEP parts[2]
    }
    asort(series_order)

    if (!first) {
      print "    ," > output
    }
    first = 0
    printf "    {\n      \"bucket_start\": \"%s\",\n", epoch_to_rfc3339(b) > output
    print "      \"series\": [" > output

    for (si = 1; si <= sc; si++) {
      split(series_order[si], parts, SUBSEP)
      tenant = parts[1]
      metric = parts[2]
      key = b SUBSEP tenant SUBSEP metric
      if (si > 1) {
        print "        ," > output
      }
      printf "        {\n" > output
      printf "          \"tenant\": \"%s\",\n", tenant > output
      printf "          \"metric\": \"%s\",\n", metric > output
      printf "          \"sum\": %s,\n", fmt_num(sum_v[key]) > output
      printf "          \"count\": %d,\n", count_v[key] > output
      printf "          \"min\": %s,\n", fmt_num(min_v[key]) > output
      printf "          \"max\": %s\n", fmt_num(max_v[key]) > output
      printf "        }" > output
    }
    print "" > output
    print "      ]" > output
    printf "    }" > output
  }
  print "" > output
  print "  ]," > output
  print "  \"footer\": {" > output
  printf "    \"total_events\": %d,\n", events_accepted > output
  printf "    \"total_value_sum\": %s,\n", fmt_num(footer_sum) > output
  printf "    \"run_seq\": %d\n", run_seq > output
  print "  }" > output
  print "}" > output
}

{
  line = $0
  sub(/\r$/, "", line)
  if (line == "") {
    next
  }

  bucket = json_field(line, "bucket") + 0
  tenant = json_field(line, "tenant")
  metric = json_field(line, "metric")
  value = json_field(line, "sum") + 0
  count = json_field(line, "count") + 0
  minv = json_field(line, "min") + 0
  maxv = json_field(line, "max") + 0

  key = bucket SUBSEP tenant SUBSEP metric

  sum_v[key] = value
  count_v[key] = count
  min_v[key] = minv
  max_v[key] = maxv
}

END {
  emit_report()
}
