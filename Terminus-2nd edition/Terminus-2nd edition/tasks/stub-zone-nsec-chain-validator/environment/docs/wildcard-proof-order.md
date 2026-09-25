# Wildcard proof order

Wildcard labels in NSEC records (owners beginning with *.) provide positive answers only after denial proofs fail.

Evaluation order for a query name and type:

1. Find a covering NSEC record where canonical owner is less than canonical qname and canonical qname is less than canonical next (including wrap-around at the zone apex). When the queried name falls in that owner–next interval but is not equal to the NSEC owner, denial succeeds without consulting the type bitmap. Only when canonical qname equals canonical NSEC owner may the type bitmap be used: if the qtype appears in the type bitmap, the name is treated as present and NSEC denial fails; if the qtype is absent, denial succeeds.
2. If no NSEC match, evaluate NSEC3 covering using zone params.
3. Only if both denial paths fail, consider wildcard NSEC owners. Wildcard match suffix must equal the qname suffix under the wildcard stem.

Wildcard must not short-circuit step 1 or 2. A query expecting invalid with a valid NSEC3 denial must not be marked valid solely because a wildcard record exists later in the capture.
