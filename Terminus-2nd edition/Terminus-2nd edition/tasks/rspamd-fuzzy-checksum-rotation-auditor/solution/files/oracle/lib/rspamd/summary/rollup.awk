BEGIN {
  FS = "\t"
  row_count = 0
}
{
  row_count++
}
END {
  print row_count > out_path
  print row_count >> out_path
}
