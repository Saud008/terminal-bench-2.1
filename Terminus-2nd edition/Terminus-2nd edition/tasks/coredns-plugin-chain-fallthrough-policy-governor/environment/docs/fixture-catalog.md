# Fixture catalog



Templates under `/app/fixtures/templates/` use `__TOKEN__` for per-run labels. These files are immutable during evaluation; the verifier checks SHA-256 digests from `/app/fixtures/template-integrity.json` using Python `hashlib` before behavioral tests and copies rendered Corefiles to `/tmp`.



| template | zone pattern |

|----------|--------------|

| `apex-fallthrough.core` | `{token}.example.test` |

| `rewrite-order.core` | `corp.{token}.example.test` |

| `rewrite-stop.core` | `stop.{token}.example.test` |

| `whoami-error.core` | `whoami.{token}.example.test` |

| `cache-rcode.core` | `cache.{token}.example.test` |

| `rewrite-cache-key.core` | `rk.{token}.example.test` |



Each `.core` file has a matching `.hosts` file when a hosts path is referenced. Bundled hosts files map probe names to loopback addresses such as `127.0.0.9`, `127.0.0.10`, `127.0.0.11`, `127.0.0.12`, `127.0.0.13`, `127.0.0.14`, `127.0.0.77`, and `127.0.0.88`.



The verifier sets `VERIFIER_SEED` (default `coredns-chain-seed-42`) to derive per-run `__TOKEN__` labels and UDP ports. Behavioral tests hash that seed when rendering templates to `/tmp`.



The governor binary path is `/usr/local/bin/dnsplugd`. Rebuild it from `/app` with `go build` when sources change.



Verifier-only templates (not under `/app/fixtures/templates/`) live under `/opt/verifier-fixtures/coredns-chain/` for hidden apex fallthrough and cache checks. Files include `hidden-apex.core`, `hidden-apex.hosts`, `hidden-cache-nx.core`, and `hidden-cache-nx.hosts`. Rendered scratch files use names such as `apex-fallthrough.hosts`, `-apex-fallthrough.hosts`, `hidden-apex.hosts`, `-hidden-apex.hosts`, `hidden-cache.core`, `-hidden-cache.core`, `hidden-cache.hosts`, and `-hidden-cache.hosts` under `/tmp`. Probe labels include `hidden-cache-known`, `hidden-apex`, `proc`, `ref-rewrite-order`, `ref-rewrite-stop`, `rewrite-cache-hit`, `rewrite-cache-nx`, and query stems such as `known.hidden.cache.`, `probe.bad.whoami.`, and `probe.noclient.whoami.`. Whoami success answers include `client=127.0.0.1` TXT payloads. `TB3_FIXTURES_DIR` may override that root when set to an absolute directory path.



Integrity manifest `template-integrity.json` lists SHA-256 digests for every bundled template pair. The helper module `integrity_digest.py` documents the same `hashlib` contract used during evaluation.

