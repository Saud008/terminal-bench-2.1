from offlineimap_manifest import ManifestRow


def select_messages(
    rows: list[ManifestRow],
    eligible_folders: set[str],
    cutoff_utc: int,
) -> list[ManifestRow]:
    out: list[ManifestRow] = []
    for row in rows:
        if row.folder not in eligible_folders:
            continue
        if row.internal_date >= cutoff_utc:
            out.append(row)
    return out


def export_summary(
    meta: dict,
    selected: list[ManifestRow],
    reference_epoch: int,
    maxage_sec: int,
    tz_offset: int,
    dry_run: bool,
    cutoff_utc: int,
) -> dict:
    folders = sorted({row.folder for row in selected})
    return {
        "schema": 1,
        "account": meta["account"],
        "reference_epoch": reference_epoch,
        "maxage_sec": maxage_sec,
        "tz_offset": tz_offset,
        "dry_run": dry_run,
        "synced_messages": len(selected),
        "synced_bytes": sum(row.size_bytes for row in selected),
        "folders": folders,
        "cutoff_utc": cutoff_utc,
    }
