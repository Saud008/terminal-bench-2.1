# Offline delivery contract

Subscription atlas rows include client_id, filter, topic, matched, retained_payload, and qos. Offline ledger rows are emitted for matching subscribers when a PUBLISH passes QoS gating. delivery_seq is monotonic in emission order. Rows sort by delivery_seq in export files.
