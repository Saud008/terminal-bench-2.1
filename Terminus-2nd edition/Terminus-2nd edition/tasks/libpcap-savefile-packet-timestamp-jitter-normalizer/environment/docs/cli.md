Binary name pcapjitter from /app/target/debug/pcapjitter (release not required).

Subcommands:

ingest --input PATH --staging PATH --ledger-root PATH

export --output PATH --staging PATH --ledger-root PATH

Environment overrides documented in tolerance-window.md, truncation-penalty.md, and gap-ledger.md apply to both subcommands.

When TB3_PCAP_DIR is an absolute path, ingest resolves --input as a basename within that directory only.

Default paths: staging /app/state/pcap-stage.json, ledger root /app/state, output /app/output/timeline.json.
