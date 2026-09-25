from __future__ import annotations


def timeline(events: list[dict[str, str]], focus_id: str) -> list[dict[str, str]]:
    out = [event for event in events if event["accession_id"] == focus_id]
    return sorted(
        out,
        key=lambda event: (event["event_date"], event["technician"], event["notes"]),
    )
