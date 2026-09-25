# Wildcard constraints

Double asterisk is forbidden. For namespace principals user@domain, asterisk is allowed only as the entire user segment or as a suffix wildcard on the domain segment matching *.example.com style. Embedded asterisks inside a user or domain token (for example bad*token) must be rejected with reason wildcard_denied before principal matching.
