Edge DNS facilities rely on each operator to deliver authoritative answers from CoreDNS-style plugin chains. Implement the dnsplugd plugin chain governor under /app/cmd/dnsplugd so UDP queries honor fallthrough eligibility, rewrite continue semantics, cache key policy, and whoami failure mapping documented in /app/docs/corefile-format.md. Chain logic lives under /app/internal/chain/ and plugins under /app/internal/plugins/. Build installs the governor at /usr/local/bin/dnsplugd.



Fixture templates under /app/fixtures/templates/ use __TOKEN__ labels; layout and SHA-256 integrity manifest are described in /app/docs/fixture-catalog.md. Procedural labels and hidden probe roots follow /app/docs/fixture-catalog.md and /app/docs/corefile-format.md. Do not edit /app/docs/, /app/fixtures/templates/, or /tests. The verifier checks template integrity before behavioral tests and copies rendered Corefiles into /tmp with per-run labels.



For queries that traverse rewrite plugins, cache keys and fallthrough eligibility follow the effective query name shown in /app/docs/corefile-format.md. Example: dnsplugd serve --corefile /tmp/test.core --listen 127.0.0.1:1053 then dig @127.0.0.1 -p 1053 apex.example.test A +norecurse.

