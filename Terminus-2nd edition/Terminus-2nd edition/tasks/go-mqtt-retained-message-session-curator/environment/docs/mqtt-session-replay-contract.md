# MQTT session replay contract

Identical broker journal replays must produce byte-identical subscription-atlas.jsonl and delivery-ledger.jsonl. The replay digest chains broker slug, scenario name, canonical atlas rows, and ledger rows using stable JSON key order. Duplicate PUBLISH packet identifiers must not create extra ledger rows after merge-session deduplication.
