# Unsupported iptables features

The mapper does not translate these iptables match modules to nft; ingest records them in `unsupported_features` and skips tuple emission for that rule line:

| Module | Reason |
|--------|--------|
| recent | no deterministic nft recent() mapping in this profile |
| limit | rate limits omitted from nft excerpt profile |
| mark | skb mark matching excluded |
| addrtype | beyond simplified profile |

Detection is triggered by `-m <name>` on an `-A` rule line.

Export copies `unsupported_features` verbatim into the report `unsupported` array (sorted lexicographically).

Rules with unsupported modules still increment a skipped counter in ingest logs but do not appear in iptables-tuples.ndjson.
