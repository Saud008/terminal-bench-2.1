# Engineering problem contract

## Core engineering concept

Simulate broker-side MQTT 3.1.1 semantics from frozen packet journals: wildcard plus and hash filter matching, retained PUBLISH overwrite and delete, QoS1 PUBACK and QoS2 PUBCOMP inflight deduplication, and session expiry suppression of offline deliveries. This is not a workflow cache auditor, execution bust ledger, or Nextflow resume tool.

## Packet-driven state machine

| MQTT phase | Modeled behavior |
|------------|------------------|
| CONNECT | client_id, clean_session |
| SUBSCRIBE | register filters; flush matching retained payloads to atlas |
| PUBLISH retain=true | update or delete retained topic store |
| PUBLISH QoS1/2 | track packet_id until PUBACK/PUBCOMP |
| DISCONNECT | close session; apply expiry window to offline queue |

## Root cause envelope

Failures surface as mismatches between journal packet order, on-disk staging snapshots, merge audit records, and exported atlas or ledger bytes. Reconcile behavior through the cited module contracts instead of treating export output as a direct replay of raw inputs.

## Verifier constraint

Identical broker journals must yield byte-identical subscription-atlas.jsonl and delivery-ledger.jsonl. TB3_SESSION_EXPIRY_MS overrides expiry only on verifier fixtures.
