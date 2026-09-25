# Reel alias registry

Alias map files contain one alias=vault_id pair per line. Comments start with #.

Stage resolves EDL reel names through the alias table before source manifest lookup. Bidirectional resolution must map vault_id names back to alias keys when sources are keyed by alias labels.

Alias resolution is case sensitive. Empty lines are ignored.
