BEGIN {
  OFS = ","
}
/^:/ {
  chain = $1
  sub(/^:/, "", chain)
  policy = $2
  # chain declaration counters omitted in this slice
  printf("{\"chain\":\"%s\",\"ordinal\":0,\"policy\":\"%s\",\"match_key\":\"\",\"target\":\"%s\",\"counter_packets\":0,\"counter_bytes\":0,\"hook_priority\":0}\n", chain, toupper(policy), toupper(policy))
  next
}
/^-A / {
  line = $0
  sub(/^-A /, "", line)
  split(line, parts, " ")
  chain = parts[1]
  rest = substr(line, length(chain) + 2)
  pkts = 0; bytes = 0
  if (match(rest, /\[[0-9]+:[0-9]+\]/)) {
    ctr = substr(rest, RSTART + 1, RLENGTH - 2)
    split(ctr, ab, ":")
    pkts = ab[1] + 0
    bytes = ab[2] + 0
    sub(/ \[[0-9]+:[0-9]+\]/, "", rest)
  }
  target = "UNSPEC"
  if (match(rest, /-j [^ ]+/)) {
    target = toupper(substr(rest, RSTART + 3, RLENGTH - 3))
  }
  ord[chain]++
  printf("{\"chain\":\"%s\",\"ordinal\":%d,\"policy\":null,\"match_key\":\"%s\",\"target\":\"%s\",\"counter_packets\":%d,\"counter_bytes\":%d,\"hook_priority\":0}\n", chain, ord[chain], rest, target, pkts, bytes)
}
