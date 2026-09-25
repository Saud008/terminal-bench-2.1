BEGIN {
  FS = "[ \t]+"
  OFS = "\t"
}
/^[[:space:]]*$/ { next }
/^[[:space:]]*TITLE:/ { next }
/^[[:space:]]*FCM:/ { next }
{
  if (NF < 8) next
  edit = $1
  reel = $2
  track = $3
  trans = $4
  rec_in = $5
  rec_out = $6
  src_in = $7
  src_out = $8
  gsub(/\r/, "", reel)
  print edit, reel, track, trans, rec_in, rec_out, src_in, src_out
}
