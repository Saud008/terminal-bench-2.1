# Platform rubric — coredns-plugin-chain-fallthrough-policy-governor

**Task folder:** tasks/coredns-plugin-chain-fallthrough-policy-governor/

Agent applies fallthrough at zone apex and subordinate names equally, +3
Agent keys cache entries on post-rewrite effective query name and QTYPE, +3
Agent preserves NXDOMAIN and SERVFAIL on cache hits without upgrading to NOERROR, +2
Agent runs rewrite with continue before fallthrough reaches hosts, +3
Agent returns SERVFAIL for whoami rejected qnames and unavailable client metadata, +2
Agent builds plugin chain in Corefile declaration order without resorting plugins, +2
Agent evaluates fallthrough eligibility against effective name after rewrite plugins, +2
Agent rebuilds dnsplugd after editing chain or plugin packages, +2
Agent edits protected fixture templates under /app/fixtures/templates to pass checks, -5
Agent modifies tests or contract docs instead of implementing plugin semantics, -5
Agent hardcodes dig answers without executing the plugin chain, -5
Agent patches only cache while fallthrough and rewrite ordering still diverge, -3
