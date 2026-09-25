BEGIN {
  FS = "\t"
  OFS = "\t"
  cutoff = reference_epoch - maxage_sec
}
{
  idate = $2 + 0
  if (idate >= cutoff) {
    print
  }
}
