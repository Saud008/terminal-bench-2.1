# sipcdrctl

Host-local SIP CDR ops desk (system administration): admit transcript packs, gate fork/provisional/terminate/retransmit/skew rules, then emit a sealed SQLite CDR publish.

- Binary: `/app/bin/sipcdrctl`
- Policy modules: `/app/lib/sipcdr/`
- Ops contracts: `/app/docs/`
- Staging: `/app/state/dialog-buffer.json`
- Outputs: `/app/output/cdr.sqlite`, `/app/output/cdr-publish-seal.json`
