Edge-router fleet operators run the host-local bgpcut peer-cutover witness at /usr/local/bin/bgpcut. Repair the cutover workflow on the working /app baseline so peer inventories under /app/fixtures/peers/ evaluate correctly and produce sealed operational reports that match the contracts under /app/docs/. There is no live BIRD session or remote peering; this is a system-administration host-local BGP cutover witness control plane, not a generic service repair exercise.

Read /app/docs/cutover-auditor-contract.md, /app/docs/peer-wave-order.md, /app/docs/filter-inheritance.md, /app/docs/aspath-match-modes.md, /app/docs/community-rewrite-rules.md, /app/docs/med-ceiling.md, /app/docs/critical-deny-abort.md, /app/docs/ledger-and-seal.md, /app/docs/cli-exits.md, /app/docs/fixture-notes.md, and /app/docs/audit-digest-hash.md before changing behavior. Report schema fields and digests are defined in those contracts.

Primary ops pass:

  bgpcut cutover --scenario <name> --output <path>

Optional:

  bgpcut cutover --scenario <name> --output <path> --run-id <id>

Scenario inventories are /app/fixtures/peers/<name>/inventory.json. Peer-id salt comes from env TB3_PEER_SALT when present; otherwise config key peer_id_salt in /app/config/bgpcut.json applies. The control plane persists /app/state/cutover-ledger.json then writes the sealed report to --output (default /app/output/bgp_cutover_report.json when omitted). Reported fields and digests must match the contracts under /app/docs/ for every bundled and hidden peer inventory.

Install the binary at /usr/local/bin/bgpcut from the Go sources under /app. Independent contract math used by the verifier lives only under /tests (cutover_contract_math.py and bgpcut_support.py; hashlib is used there for audit_digest, matching /app/tools/audit_digest_ref.py). Do not modify /app/docs/, /app/config/, or /app/fixtures/. Decoy packages under the Go module tree are not on the hot path.
