"""Size-limit admission gate."""

from __future__ import annotations


class OversizedError(Exception):
    pass


def ensure_fits(catalog: dict, marks: list[dict]) -> None:
    limit = catalog["max_mark_px"]
    for mark in marks:
        if mark["padded_w"] > limit or mark["padded_h"] > limit:
            raise OversizedError(
                f"{mark['mark_id']}:{mark['frame']} exceeds max {limit}"
            )
