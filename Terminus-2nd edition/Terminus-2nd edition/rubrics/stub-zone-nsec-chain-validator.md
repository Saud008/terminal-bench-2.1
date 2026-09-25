# Platform rubric — stub-zone-nsec-chain-validator

**Task folder:** tasks/stub-zone-nsec-chain-validator/

Agent sorts NSEC owners with wire.Canonical before validating next links, +3
Agent excludes wildcard NSEC owners from chain validation ordering, +3
Agent compares NSEC next fields with canonical owner names not raw strings, +3
Agent checks per-record NSEC3 iterations against zone params before CoversQname, +3
Agent keys stub denial cache by canonical qname and qtype together, +3
Agent flushes denial cache when SOA serial regresses, +3
Agent walks NSEC denial proofs before wildcard expansion, +3
Agent handles wrap-around NSEC and NSEC3 hash ranges at zone apex, +2
Agent rebuilds nsecval in test.sh after Go edits, +2
Agent writes chain-snapshot.json during validate before query walk, +2
Agent ignores proof/wrap.go decoy helper for production validate path, +1
Agent patches only nsec/order.go while walker order stays wildcard-first, -3
Agent fixes cache serial observe without clearing map on regression, -3
Agent accepts NSEC3 proof when record iterations differ from zone params, -3
Agent caches query results keyed by qname only ignoring qtype, -2
