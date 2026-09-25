# Expiry windows

VEX statements may include expires_at as RFC3339 UTC timestamps ending with Z.

A statement is active when expires_at is absent or when current UTC time is strictly before expires_at. When expires_at equals current UTC instant, the statement is expired and ignored.

Expired statements do not participate in precedence selection.

Waiver evidence on impact rows copies statement_id and expires_at only when the winning statement is not_affected or fixed and still active.

Fixed statements without expires_at are always active.
