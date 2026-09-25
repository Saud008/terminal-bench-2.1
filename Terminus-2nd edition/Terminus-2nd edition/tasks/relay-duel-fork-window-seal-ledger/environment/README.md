# duelctl

Offline relay-duel playfield desk for the games playtest: admit duel admit-log packs, gate lane-fork / hold / resign-forfeit / retransmit / skew rules, then emit a sealed SQLite match-ledger publish.

- Binary: `/app/bin/duelctl`
- Policy modules: `/app/lib/duelctl/`
- Playfield contracts: `/app/docs/`
- Staging: `/app/state/match-buffer.json`
- Outputs: `/app/output/match-ledger.sqlite`, `/app/output/match-publish-seal.json`
