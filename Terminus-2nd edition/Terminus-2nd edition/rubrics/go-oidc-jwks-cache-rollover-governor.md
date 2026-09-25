# Platform rubric — go-oidc-jwks-cache-rollover-governor

**Task folder:** tasks/go-oidc-jwks-cache-rollover-governor/

Agent replays JWKS timeline transcripts into transcript-staging.json with sealed digest, +3
Agent hydrates cache snapshot cumulatively across every timeline event not only the last, +3
Agent matches kid values case-insensitively across active and retired pools, +3
Agent binds issuer strings with trimmed lowercase comparison, +2
Agent requires every token audience to appear in policy when audiences is non-empty, +3
Agent rejects active keys when cache max-age seconds are exceeded, +3
Agent accepts retired keys inside inclusive grace bounds after rollover, +3
Agent rejects revoked kids before grace even when previously retired, +3
Agent blocks emit-report export when hydrate_revision is zero, +2
Agent sorts governance report decisions by token_id ascending, +2
Agent produces byte-identical report on idempotent second emit, +2
Agent reads TB3 hidden fixtures for grace boundary and revoked-during-grace traps, +2
Agent rebuilds oidcgov via verifier-rebuild.sh before pytest, +1
Agent leaves wrap telemetry decoy off verification hot path, +1
Agent sorts timeline events by descending epoch breaking transcript digest, -3
Agent hydrates only the final timeline event dropping earlier keys, -3
Agent accepts tokens with partial audience overlap when policy lists multiple audiences, -3
Agent accepts retired kids outside grace window with grace_key verdict, -3
Agent emits governance report before hydrate-cache increments revision, -3
Agent uses non-canonical Dockerfile base image, -5
