BEGIN {
  FS = "\t"
  OFS = "\t"
  effective = window_size + 0
}
{
  mail_id = $1
  body = $2
  len = length(body)
  if (len < effective) next
  for (i = 0; i <= len - effective; i++) {
    shingle = substr(body, i + 1, effective)
    print mail_id, shingle
  }
}
