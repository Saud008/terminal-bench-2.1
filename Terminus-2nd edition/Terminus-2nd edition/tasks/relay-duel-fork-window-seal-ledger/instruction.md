Relay duel fork-window seal ledger playtest

Build the relay duel fork-window seal ledger playtest, an offline arena duel playfield planner for admit-log admission, duel_id/fork-tag lane forks, hold-signal and resign-forfeit scoring, retransmission collapse, skew-corrected rush/calm score-window fences, and sealed SQLite match-ledger win-condition export on the working baseline under `/app`. The planner loads duel admit-log scenario packs, applies lane-fork and hold scoring, audits FORFEIT-versus-RESIGN and retransmit traps, then seals `seal-ledger` playtest exports when the match-seal win condition is met. There is no live duel socket and no outbound network. This is a games relay-duel playfield playtest and sealed-ledger win-condition workflow: keep admit-log admission, lane-fork traps, hold suppression, resign-forfeit precedence, retransmit collapse, skew-corrected rush/calm windows, match-buffer staging seals, and sealed match-ledger atlas export aligned. It is not a software-engineering module rebuild, not a data-processing pipeline, not a system-administration ops desk, not a debugging drill, and not a build-and-dependency-management exercise.

The graded binary is `/app/bin/duelctl`. Playtest verbs:

```text
duelctl admit-log --arena ARENA --scenario SLUG
duelctl fold-branches --arena ARENA --scenario SLUG
duelctl score-windows --arena ARENA --scenario SLUG
duelctl seal-ledger --arena ARENA --scenario SLUG
```

Playfield contracts under `/app/docs/` define the enforceable win-condition rules:

- `/app/docs/lane-fork-contract.md` — join keys and forked fork-tag branches
- `/app/docs/hold-signal-contract.md` — hold gating (no ledger without accept); wire status 180/183 are hold, 2xx is accept
- `/app/docs/resign-forfeit-precedence-contract.md` — FORFEIT versus RESIGN precedence
- `/app/docs/retransmit-suppression-contract.md` — retransmission collapse
- `/app/docs/clock-skew-contract.md` — skew correction before score windows
- `/app/docs/score-window-contract.md` — rush/calm window rating
- `/app/docs/cli-surface.md` — playtest verb surface and flags
- `/app/docs/duel-admit-log-format.md` — admit-log wire format
- `/app/docs/match-buffer-pipeline.md` — match-buffer staging artifact shape
- `/app/docs/match-ledger-sqlite-schema.md` — sealed SQLite match-ledger schema
- `/app/docs/verifier-refmath-contract.md` — reference math used by the verifier
- `/app/docs/playfield-failure-contract.md` — playfield failure modes

`admit-log` writes `/app/state/match-buffer.json`. `fold-branches` updates that buffer and stamps `match_seal`. `score-windows` writes `/app/work/score-window-report.json` and refreshes staging. `seal-ledger` publishes `/app/output/match-ledger.sqlite` and `/app/output/match-publish-seal.json` only from that staged playfield state when `match_seal` is greater than zero. Only answered matches with a final disposition may appear in published ledger rows. Hold-only legs must remain absent from SQLite output. A second sealed pass on unchanged inputs must keep `match-ledger.sqlite` byte-stable. Policy modules live under `/app/lib/duelctl/`; the decoy helper stays off the admit, gate, and emit path.

Bundled playfield packs live under `/app/fixtures/`. Off-catalog traps under `/opt/verifier-fixtures/duelctl/` follow the same contracts. When `TB3_FIXTURE_DIR` is set, fixture roots may override for verifier-only overlays. After policy-module edits under `/app/lib/duelctl/`, leave `/app/bin/duelctl` current. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`. Offline only.
