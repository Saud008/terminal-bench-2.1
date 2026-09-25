# Paper lineage

Paper manifest JSON contains batches array entries with id, parent, and gamma_anchor.

effective_gamma for a batch_id walks parent links starting at the batch until gamma_anchor is non-null. Cycles must not loop forever.

When abs(effective_gamma minus profile gamma_reference) exceeds gamma_drift_threshold from policy, evaluation adds GAMMA_LINEAGE_DRIFT.
