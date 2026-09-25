# Heat balance ledger fields

publish-ledger writes JSON with run_id, kiln_id, energy_in_mj, clinker_out_t, heat_loss_mj, residual_mj, residual_mj_per_t, fuel_batches, probe_windows, lineage_digest, audit_digest.

lineage_digest is SHA256 hex over sorted probe_ts:batch_id pairs joined by pipe.

audit_digest is SHA256 hex over JSON with keys run_id, energy_in_mj, clinker_out_t, heat_loss_mj, residual_mj_per_t, lineage_digest sorted.
