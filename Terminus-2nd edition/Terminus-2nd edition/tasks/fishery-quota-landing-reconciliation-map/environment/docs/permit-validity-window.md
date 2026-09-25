# Permit validity window

A landing is permit-valid when landed_at date (first ten characters YYYY-MM-DD) is greater than or equal to valid_from and less than or equal to valid_until inclusive.

The vessel must hold a permit entry. The resolved species key must appear in the permit species list case-insensitively.

Reject with permit_expired when outside the window, species_not_permitted when species missing, missing_permit when vessel absent.
