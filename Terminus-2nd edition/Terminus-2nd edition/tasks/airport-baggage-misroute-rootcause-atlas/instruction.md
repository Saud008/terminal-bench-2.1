Task identity a7b3d91e scopes the airport baggage misroute root-cause atlas capability. See /app/docs/engineering-problem-contract.md for scope boundaries.

Operations control for a multi-terminal hub must correlate RFID bag-tag reads, sortation belt assignments, inbound-to-outbound connection tables, published minimum connect intervals, and station sortation outages before loaders reroute stranded luggage. This fleet operational workflow implements bag-atlas on the working Rust tree at /app using the five-layer trace audit in /app/docs/baggage-trace-audit-lattice.md and the routing lattice in /app/docs/baggage-routing-lattice.md: persist hub layout latches, transform scan timelines into a deterministic scan ledger, bind belt segments to scheduled flights while evaluating connection windows and outage masks, and publish classified misroute findings as JSON under /app/output/.

Install bag-atlas at /app/bin/bag-atlas with subcommands hub-latch, seq-scans, route-belts, and emit-rootcause. Hub layout fields, scan stream rows, scan sequence tie breaks, belt weight selection, connection window derivation, outage half-open windows, misroute class stack, and atlas digest fields follow /app/docs/hub-layout-schema.md, /app/docs/scan-stream-format.md, /app/docs/scan-sequence-contract.md, /app/docs/belt-route-lattice.md, /app/docs/mct-feasibility-contract.md, /app/docs/connection-window-derivation.md, /app/docs/outage-window-contract.md, /app/docs/root-cause-taxonomy.md, /app/docs/misroute-class-stack.md, /app/docs/baggage-trace-audit-lattice.md, /app/docs/atlas-output-fields.md, /app/docs/fixture-hub-catalog.md, /app/docs/baggage-routing-lattice.md, and /app/docs/pytest-verifier-primitives.md.

bag-atlas hub-latch reads hub_topology.json and writes /app/state/hub-latch/<hub-id>.json with topology_revision tracking.

bag-atlas seq-scans reads scans.jsonl, applies duplicate scan_seq supersession by relay_pass, sequences rows by scan_minute then scan_seq, and writes /app/work/scan-ledger/<hub-id>.jsonl.

bag-atlas route-belts reads the scan ledger and hub latch, selects belt targets by belt weight, evaluates connection window feasibility against published connection rows, masks scans during station outage windows, and writes /app/work/route-lattice/<hub-id>.jsonl.

bag-atlas emit-rootcause reads route lattice rows, applies the misroute class stack, excludes outage-suppressed rows from misroute totals, and writes root-cause atlas JSON to the caller --output path ending with -rootcause-atlas.json.

Bundled hub scenarios live under /app/fixtures/hubs/ per /app/docs/fixture-hub-catalog.md. Runtime hub roots honor TB3_HUB_ROOT. Minimum connection overrides honor TB3_MCT_MINUTES. Outage boundary probes honor TB3_OUTAGE_STATION. Hub latch artifacts persist under /app/state/hub-latch/ and atlas JSON under /app/output/.

Compile bag-atlas with cargo build --release --locked from /app and install the binary to /app/bin/bag-atlas. Entry source lives at /app/src/a7_main.rs. Run /app/scripts/reset-workspace.sh before cross-run verifier cases. The weight forecast decoy module is not used by hub-latch, seq-scans, route-belts, or emit-rootcause.

Verifier harness modules tests/conftest.py and tests/baggage_oracle.py implement independent reference recomputation; hashlib digests follow /app/docs/pytest-verifier-primitives.md and /app/tools/atlas_digest_ref.py.
