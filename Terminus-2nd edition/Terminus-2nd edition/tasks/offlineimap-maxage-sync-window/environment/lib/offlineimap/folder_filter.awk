BEGIN {
  FS = "\t"
  while ((getline line < rules_path) > 0) {
    if (line ~ /^[[:space:]]*#/ || line ~ /^[[:space:]]*$/) continue
    split(line, parts, " ")
    if (parts[1] == "include") {
      inc[++nic] = parts[2]
    } else if (parts[1] == "exclude") {
      exc[++nexc] = parts[2]
    }
  }
  close(rules_path)
}
{
  folder = $1
  keep = 1
  for (i = 1; i <= nic; i++) {
    if (folder ~ inc[i]) keep = 0
  }
  for (i = 1; i <= nexc; i++) {
    if (folder ~ exc[i]) keep = 0
  }
  if (keep) print
}
