# Disabled model handling

Manifest packs may mark models with enabled false. Disabled models remain in checkpoint catalogs for curator review but must not appear in model_order.

disabled_ref_ok summary flag is false when any enabled model depends_on references a disabled model unique_id. Source dependencies never affect disabled_ref_ok even when the source row is stale.

When disabled_ref_ok is false, export bundles must include DISABLED_UPSTREAM alerts. Each alert:

  - alert_code: DISABLED_UPSTREAM
  - severity: error
  - subject_id: the enabled downstream model unique_id
  - message: exactly `depends on disabled {disabled_upstream_unique_id}` where the placeholder is the seed-scoped disabled upstream unique_id

One DISABLED_UPSTREAM alert per (enabled downstream, disabled upstream) depends_on edge.

Enabled models that depend only on sources and other enabled models keep disabled_ref_ok true.

Exposure closure still walks through disabled models when collecting exposure_refs; only model_order excludes them.
