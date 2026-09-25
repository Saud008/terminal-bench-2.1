Edge-router fleet operators run the host-local bgpcut peer-cutover witness at /usr/local/bin/bgpcut. Repair the cutover workflow on the working /app baseline so peer inventories under /app/fixtures/peers/ evaluate correctly and produce sealed operational reports. There is no live BIRD session or remote peering; this is a system-administration host-local BGP cutover witness control plane, not a generic service repair exercise.

Supporting field layouts and CLI notes live under /app/docs/ (cutover-auditor-contract, peer-wave-order, filter-inheritance, aspath-match-modes, community-rewrite-rules, med-ceiling, critical-deny-abort, ledger-and-seal, cli-exits, fixture-notes, audit-digest-hash). Graded cutover behavior must satisfy the rules below.

Primary ops pass:

  bgpcut cutover --scenario <name> --output <path>

Optional:

  bgpcut cutover --scenario <name> --output <path> --run-id <id>

Scenario inventories are /app/fixtures/peers/<name>/inventory.json. Peer-id salt comes from env TB3_PEER_SALT when present; otherwise config key peer_id_salt in /app/config/bgpcut.json applies. Append that salt to every peer_id and every RIB peer_id before evaluation. The control plane persists /app/state/cutover-ledger.json then writes the sealed report to --output (default /app/output/bgp_cutover_report.json when omitted).

Wave admission orders peers by wave_rank ascending, then asn ascending, then peer_id ascending after salt. That sequence is peer_order on both the ledger and the sealed report.

Filter inheritance starts from the peer group filters for peer.group_id. A peer-local filter with the same filter_id replaces the group entry; new filter_id values are added. Sort the merged list by priority descending, then filter_id ascending. The first matching filter wins; if none match, the action is deny.

AS-path match modes:

- origin: the last ASN in as_path equals filter.asn
- transit: filter.asn appears in as_path excluding the final origin ASN (path length at least 2)
- exact: as_path equals filter.as_path element-wise

On accept, apply peer.community_rewrite by walking map keys in lexicographic ascending order and replacing exact community string matches. Never rewrite communities whose ASN part is 0 or 65535. After rewrite, if med_ceiling is not null, set med to the lesser of med and med_ceiling. Denied routes keep their original med and communities.

Before evaluation, keep a checkpoint copy of the salted RIB. If a deny hits a prefix listed in critical_prefixes and peer.abort_on_critical_deny is true, include that deny row with aborted=true, set wave_aborted=true, restore rib_after from the checkpoint (discard earlier accept mutations), and stop the wave.

Seal the report from the ledger peer_order and row order. Do not re-sort peer_order or digest rows during seal. audit_digest is lowercase hex sha256 of UTF-8 lines peer_id|prefix|action|as_path-commas joined by newlines with no trailing newline, in ledger row order.

CLI exits: 0 success, 1 usage or unknown command, 2 missing scenario inventory, 3 invalid inventory JSON.

Install the binary at /usr/local/bin/bgpcut from the Go sources under /app. Independent contract math used by the verifier lives only under /tests. Do not modify /app/docs/, /app/config/, or /app/fixtures/. Decoy packages under the Go module tree are not on the hot path.
