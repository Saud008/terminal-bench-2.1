Court records security officers run the host-local filingatlas sealed-disclosure control plane at /app/bin/filingatlas. Each offline security pass admits a sealed filing bundle, expands party-alias reachability so masked identities cannot bypass redaction policy, scans paginated filing text for sealed-term exposure and exhibit cross-reference leakage, and publishes a digest-bound redaction-risk atlas ranked for clerk triage before public docket release. There is no live PACER or CM/ECF connection. This is a security sealed-record disclosure gate; keep alias closure, sealed-term matching, citation anchors, and atlas attestation aligned. It is not a generic service repair exercise.

Security contracts under /app/docs/: disclosure-risk-ops-workflow.md for the control-plane overview, redaction-atlas-context.md for domain vocabulary, cli-surface.md for operator verbs, bundle-fingerprint-contract.md for admitted-bundle witnesses, party-alias-contract.md for alias reachability, exhibit-link-contract.md for exhibit sub-reference linkage, sealed-term-contract.md for sealed-term normalization, pageline-citation-contract.md for page-line anchors, docket-dedup-contract.md for primary docket selection, atlas-emission-contract.md for sealed atlas shape and digest, and verifier-refmath-contract.md for independent attestation math.

Primary security artifacts:

  /app/state/bundle-fingerprint.json — admitted filing-bundle witness
  /app/state/party-graph.json and /app/state/index-revision.json — alias-closure stage after party indexing
  /app/state/risk-findings.json — sealed-term and exhibit exposure findings with citation anchors
  /app/output/redaction-risk-atlas.json — digest-sealed triage atlas (emit only when index_revision > 0)

Disclosure constraints that must hold for every successful atlas:

- Party alias graphs expand transitive reachability before risk matching so alias collisions cannot hide sealed parties.
- Exhibit references include sub-exhibits such as Exhibit 12-A and roman numeral variants.
- Sealed term matching is case-insensitive with hyphen and space normalization.
- Docket selection prefers primary_flag=true entries over latest filed clock values.
- Findings carry page-line citation anchors and link to the correct party_id under party-alias-contract (party-alias-transitive → P2; party-casefold-match → P1).
- Atlas fields, ranking, and atlas_digest match atlas-emission-contract.md.

Operator surface follows /app/docs/cli-surface.md (load-bundle, index-parties, scan-risks, emit-atlas). Bundled scenarios live under /app/fixtures/scenarios. Hidden verifier probes may supply alternate roots and sealed-term sensitivity offsets at runtime. Do not edit /app/docs/ or /app/fixtures/.
