# Custody transfer log format

Each transfer event carries event_id, evidence_id, from_officer_id, to_officer_id, from_location_id, to_location_id, seal_number, expected_seal, event_epoch_ms, and event_type.

Officer identifiers must preserve original casing from the bundle. Do not lowercase officer ids during vault load.

event_type is transfer, seal_check, or lab_submit. Only transfer rows create lineage edges.
