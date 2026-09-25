#!/usr/bin/env gawk -f
# Stage 3: validate manifest and emit aggregate report from bucket rollup.

BEGIN {
  OFS = ""
  window_sec = window_sec + 0
  run_seq = run_seq + 0
  load_stats()
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

function emit_report(    buckets, b, key, parts, tenant, metric, wi, si, first, n, cat, footer_events) {
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

  footer_events = n

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
    delete series_order
    sc = 0
    for (key in sum_v) {
      split(key, parts, SUBSEP)
      if (parts[1] + 0 != b) {
        continue
      }
      series_order[++sc] = parts[2]
    }
    asort(series_order)

    if (!first) {
      print "    ," > output
    }
    first = 0
    printf "    {\n      \"bucket_start\": \"%s\",\n", epoch_to_rfc3339(b) > output
    print "      \"series\": [" > output

    for (si = 1; si <= sc; si++) {
      cat = series_order[si]
      key = b SUBSEP cat
      tenant = tenant_v[key]
      metric = metric_v[key]
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
  printf "    \"total_events\": %d,\n", footer_events > output
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

  catkey = tenant metric
  key = bucket SUBSEP catkey

  sum_v[key] = value
  count_v[key] = count
  min_v[key] = minv
  max_v[key] = maxv
  tenant_v[key] = tenant
  metric_v[key] = metric
}

END {
  emit_report()
}
