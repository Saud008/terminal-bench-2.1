BEGIN {
  FS = "\t"
  offset_sec = (env_offset == "" ? 0 : env_offset + 0)
  cutoff = reference_epoch + (tz_offset * 60) - maxage_sec + offset_sec
}
{
  idate = $2 + 0
  if (idate >= cutoff) {
    print
  }
}