from __future__ import annotations


def lineage(transfers: list[dict[str, str]], focus_id: str) -> list[str]:
    filtered = [transfer for transfer in transfers if transfer["accession_id"] == focus_id]
    filtered.sort(key=lambda transfer: transfer["transfer_date"])
    if not filtered:
        return []
    out = [filtered[0]["from_party"]]
    for transfer in filtered:
        out.append(transfer["to_party"])
    return out
