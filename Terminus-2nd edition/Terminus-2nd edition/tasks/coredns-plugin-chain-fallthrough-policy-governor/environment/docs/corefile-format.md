# CoreDNS-style server block syntax

## Wire format

```text
zone.example:1053 {
    fallthrough
    plugins rewrite whoami cache hosts
    rewrite suffix .corp .internal continue
    whoami
    cache 30
    hosts /path/to/hosts
}
```

Directives: `fallthrough`, `plugins`, `rewrite`, `whoami`, `cache`, `hosts`.

## Plugin chain semantics

- Build each server block's plugin chain in Corefile declaration order (top to bottom). Do not reverse or resort plugins.
- When a block includes `fallthrough`, both apex names (the zone origin) and subordinate names may fall through to later plugins after a non-terminal outcome. Fallthrough applies equally at the zone apex.
- The `rewrite` plugin with a `continue` flag must rewrite the query name and continue the chain; without `continue`, a matching rewrite terminates the chain with the rewritten response state.
- The `whoami` plugin returns a TXT record at `{qname}` with the client address when lookup succeeds. Failures (including rejected queries and invalid client metadata) must yield `SERVFAIL`, not `NOERROR` with an empty answer. Query names containing `.bad.` are rejected; names containing `.noclient.` are evaluated with unavailable client metadata.
- The `cache` plugin stores the full downstream response including RCODEName. Cache hits must return the same RCODE and answer RRset as the original response (do not upgrade `NXDOMAIN`/`SERVFAIL` to `NOERROR`). Cache keys use the effective query name after any rewrite in the chain (not the pre-rewrite wire name) together with the QTYPE.
- Fallthrough eligibility is evaluated against the effective query name after rewrite plugins have run, not the original wire query name.
- The `hosts` plugin answers `A`/`AAAA` from the path on its line after prior plugins allow fallthrough.
