import os


def maxage_cutoff(reference_epoch: int, maxage_sec: int, tz_offset: int) -> int:
    offset_sec = int(os.environ.get("OI_MAXAGE_OFFSET_SEC", "0") or "0")
    effective_ref = reference_epoch + (tz_offset * 60)
    return effective_ref - maxage_sec + offset_sec
