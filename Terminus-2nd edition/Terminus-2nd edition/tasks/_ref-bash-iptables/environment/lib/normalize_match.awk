BEGIN {
  FS = "\n"
}
{
  line = $0
  if (line !~ /^\{/) next
  # baseline passes match_key through without full normalization
  # Only lowercases proto= segments partially
  gsub(/RELATED/, "related", line)
  gsub(/ESTABLISHED/, "established", line)
  # ct states and dport lists not sorted yet
  print line
}
