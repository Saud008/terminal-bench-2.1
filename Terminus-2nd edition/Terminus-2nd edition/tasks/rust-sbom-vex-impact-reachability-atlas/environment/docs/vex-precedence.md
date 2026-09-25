# VEX precedence

When multiple VEX statements target the same norm_purl and vuln_id pair, pick the effective statement by status precedence before expiry filtering.

Precedence rank (highest wins):

1. not_affected
2. fixed
3. under_investigation
4. affected
5. unknown

Tie-break equal rank by latest updated_at timestamp in UTC. Lexicographically greater updated_at wins.

If no statement remains after expiry filtering, effective status is unknown with empty waiver evidence.

Export impact rows use effective_status from this precedence table.
