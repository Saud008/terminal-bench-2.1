BEGIN {
  FS = "\t"
  msg_count = 0
}
{
  msg_count++
}
END {
  print msg_count > out_path
  print msg_count >> out_path
}
