# fluxpress workflow

Phase A -- accrue-residuals: read one ring bundle JSON, compute residual channel records, and
persist /app/scratch/ring-fluence/<campaign-id>.json. When a ledger file already exists
for the campaign id, read its accrual_epoch and write accrual_epoch as the prior
value plus one.

Phase B -- emit-occupancy: read only the ring-fluence ledger JSON for the campaign id. Do not
reopen ring bundle fixtures. Emit occupancy summary fields and ranked closure rows to
the caller output path.

Veto-killed channels are recorded in the ledger with residual_counts 0 and vetoed
true. They never appear in channel_order or rows, and never contribute to the
occupancy scan.

The crate's module tree is wired in /app/src/lib.rs, which declares every real module path
(protocol, campaign_io, residual_kernel, quantize, energy_order, coincidence_veto,
occupancy_scan, fluence_ledger, closure_rank, digest_line, closure_emit) and re-exports their
public items. /app/decoy/regatlas_ir_stub.rs is a legacy stub that must stay entirely
undeclared from that module tree -- it never appears in lib.rs and sits off the
accrue-residuals / emit-occupancy hot path.
