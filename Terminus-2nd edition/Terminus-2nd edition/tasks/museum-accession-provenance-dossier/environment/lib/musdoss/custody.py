from __future__ import annotations


def lineage(transfers: list[dict[str, str]], focus_id: str) -> list[str]:
    parties: set[str] = set()
    for transfer in transfers:
        if transfer["accession_id"] != focus_id:
            continue
        parties.add(transfer["from_party"])
        parties.add(transfer["to_party"])
    return sorted(parties)
