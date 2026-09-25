Subscription-integrity security operators need a host-local entitlement trust-admission control plane at `/app/bin/subledctl`. The plane admits offline billing-cycle manifests into a tamper-evident SQLite trust journal, evaluates inclusive entitlement-window authenticity, mid-cycle credit eligibility, coupon-precedence authenticity, meter-carryover integrity, and anchor-shift admission gates, stages a tamper-evident entitlement buffer, and publishes digest-sealed subscription invoices only when `reconcile_pass` and `ledger_digest` attestation gates hold—without a remote billing host or outbound network step. This is a security entitlement-attestation and invoice-seal workflow: keep coupon authenticity, window authenticity, anti-replay publish, tamper-evident staging, and digest-bound ledger attestation aligned. It is not a generic SaaS billing engine, Go CLI rebuild, pytest harness, or CI tooling exercise.

Security contracts under `/app/docs/`:

- admission verbs and defaults: `/app/docs/cli-surface.md`
- cycle manifest admission into the trust journal: `/app/docs/cycle-load-contract.md`
- inclusive entitlement-window authenticity: `/app/docs/entitlement-window-contract.md`
- mid-cycle credit eligibility segments: `/app/docs/proration-segment-contract.md`
- coupon-precedence authenticity among exclusive and stackable offers: `/app/docs/coupon-precedence-contract.md`
- meter-carryover integrity on downgrade: `/app/docs/usage-carryover-contract.md`
- anchor-shift admission realignment: `/app/docs/anchor-shift-contract.md`
- tamper-evident entitlement buffer digests: `/app/docs/entitlement-buffer-contract.md`
- digest-sealed invoice publish and anti-replay republication: `/app/docs/invoice-publish-contract.md`
- decoy catalog isolation (must not alter trust decisions): `/app/docs/decoy-plandisplay-contract.md`
- trust-evaluation surface and hidden fixture roots: `/app/docs/trust-evaluation-surface-contract.md`
- host-local trust identity envelope: `/app/docs/entitlement-trust-identity-contract.md`

`subledctl` must expose:

```text
subledctl load-cycle --scenario <name> [--fixture-dir <dir>]
subledctl reconcile-entitlements --scenario <name>
subledctl publish-invoices --scenario <name> [--output <path>]
```

`load-cycle` must normalize the scenario into `/app/state/billing.db`. Public scenarios sit under `/app/fixtures/cycles`. `reconcile-entitlements` must enforce the window, proration, coupon, carryover, and anchor admission gates, stage `/app/work/entitlement-buffer.json`, and advance `/app/state/reconcile-pass.json` before publish. `publish-invoices` must seal `/app/output/subscription-invoices.json` plus entitlement lineage in `entitlement-ledger.jsonl` only from committed reconcile-pass state; the sealed set must be byte-stable, match independent reference entitlement math, and carry a `ledger_digest` that attests the invoice set.

Grading-critical encoding (full formulas and numeric examples are in the contracts above):

- **Segment windows:** prior segment ends the day before each plan change; the new segment starts on the change date (`entitlement-window-contract.md`).
- **Proration credit:** subtract `old_monthly * inclusive_days(change_date, cycle_end) // cycle_days` from the **new** segment’s `base_cents`; **`proration_cents` is always `0`**; never emit a separate credit line (`proration-segment-contract.md`).
- **Anchor shift:** truncate `window_end` to the first on-or-after-effective anchor candidate within the cycle, then recompute days/base (`anchor-shift-contract.md`).
- **Coupons:** best non-stackable discount on full subtotal first; stackable coupons apply sequentially on the remainder (`coupon-precedence-contract.md`).

The decoy plan-preview helpers under `internal/decoy/plandisplay` are catalog display only and must never alter reconcile or invoice-seal trust decisions. When `TB3_FIXTURE_DIR` is set, load reads scenarios from that root (including `/opt/verifier-fixtures/subledctl`). When `TB3_PRORATION_BPS` is set, verifier-only cycles may adjust proration rounding under the same authenticity gates. After authenticity-policy edits under `/app/internal/`, leave `/app/bin/subledctl` current (the verifier may invoke `/app/scripts/verifier-rebuild.sh`). Runtime trust artifacts under `/app/state`, `/app/work`, and `/app/output` must remain wipeable between independent trust evaluations via `/app/scripts/reset-state.sh`. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
