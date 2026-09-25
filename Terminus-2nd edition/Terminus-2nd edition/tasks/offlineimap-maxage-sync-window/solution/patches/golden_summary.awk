BEGIN {
  FS = "\t"
  msg_count = 0
  byte_sum = 0
}
{
  msg_count++
  byte_sum += $3 + 0
}
END {
  print msg_count > out_path
  print byte_sum >> out_path
}