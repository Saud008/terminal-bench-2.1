BEGIN {
  chain = ""
  ord["INPUT"] = 0
  ord["FORWARD"] = 0
  ord["OUTPUT"] = 0
}
/chain[ \t]+[A-Za-z]+/ {
  if (match($0, /chain[ \t]+([A-Za-z]+)/, m)) {
    chain = toupper(m[1])
    if (chain == "INPUT" || chain == "FORWARD" || chain == "OUTPUT") {
      # will emit policy when policy line seen
    } else {
      chain = ""
    }
  }
}
/policy[ \t]+(accept|drop)/ {
  if (chain != "") {
    pol = toupper($2)
    printf("{\"chain\":\"%s\",\"ordinal\":0,\"policy\":\"%s\",\"match_key\":\"\",\"target\":\"%s\",\"counter_packets\":0,\"counter_bytes\":0,\"hook_priority\":0}\n", chain, pol, pol)
  }
}
/accept$/ || /drop$/ {
  if (chain == "") next
  line = $0
  gsub(/^[ \t]+|[ \t]+$/, "", line)
  if (line ~ /^policy / || line ~ /^type / || line ~ /^hook /) next
  target = "ACCEPT"
  if (line ~ /drop/) target = "DROP"
  ord[chain]++
  printf("{\"chain\":\"%s\",\"ordinal\":%d,\"policy\":null,\"match_key\":\"%s\",\"target\":\"%s\",\"counter_packets\":0,\"counter_bytes\":0,\"hook_priority\":0}\n", chain, ord[chain], line, target)
}
