# Platform rubric — bind9-zone-include-fragment-precedence-reconciler

**Task folder:** tasks/bind9-zone-include-fragment-precedence-reconciler/

Agent expands $INCLUDE fragments depth-first with later units overriding earlier records on owner class type key, +3
Agent records processing_order interleaving master segments with include files at each include point, +3
Agent writes merge-staging.json sibling with canonical snapshot_digest on ingest, +3
Agent exports JSON from persisted ingest snapshot bytes without re-parsing zone files from disk, +3
Agent reports wildcard_conflicts when apex and wildcard records collide in merged output, +2
Agent applies SOA reload bump from master serial ignoring fragment decoy SOA values, +2
Agent validates NSEC chain continuity across include boundaries in compile output, +2
Agent stores include_fingerprint in snapshot for cache invalidation policy, +2
Agent sets compile_digest equal to canonical_snapshot_digest rather than legacy key lists, +2
Agent compiles hidden bundles resolved through ZONEFRAG_BUNDLE_ROOT override paths, +2
Agent hardcodes compile or export JSON for bundled fixtures without executing merge logic, -3
Agent re-parses zone tree files from disk during export instead of reading ingest snapshot, -3
Agent modifies files under tests/ or edits public bundle manifests to satisfy verifier checks, -5
Agent patches only include.sh while hidden wildcard bundle output still diverges from reference, -3
Agent patches only export.sh while merge-staging snapshot_digest stays wrong after ingest, -3
Agent defines compile processing_order via lexicographic order.sh instead of include-contract walk, -3
