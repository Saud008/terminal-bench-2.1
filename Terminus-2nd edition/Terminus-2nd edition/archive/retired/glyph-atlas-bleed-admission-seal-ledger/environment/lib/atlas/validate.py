"""Size-limit admission gate."""

from __future__ import annotations


class OversizedError(Exception):
    pass


def ensure_fits(catalog: dict, sprites: list[dict]) -> None:
    limit = catalog["max_sprite_px"]
    for sprite in sprites:
        if sprite["padded_w"] > limit or sprite["padded_h"] > limit:
            raise OversizedError(
                f"{sprite['glyph_id']}:{sprite['frame']} exceeds max {limit}"
            )
