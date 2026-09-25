BEGIN {
  FS = "\t"
  n = split(eligible, arr, ",")
  for (i = 1; i <= n; i++) {
  if (arr[i] != "") allowed[arr[i]] = 1
  }
}
{
  folder = $1
  if (allowed[folder]) print
}