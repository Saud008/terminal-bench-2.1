# Metrology dossier export

export writes dossier JSON with:

- batch_id
- fuse_generation copied from register
- rows: dossier rows ranked by severity descending then instrument_id ascending
- summary: instrument_count, invalid_cert_count, unauthorized_tech_count, oot_channel_total
- dossier_digest

severity equals out_of_tolerance_count times ten plus five when cert_valid is false plus three when authorized_tech is false.

Each row expanded_uncertainty must copy expanded_uncertainty from the register payload not combined_uncertainty.

dossier_digest is sixteen hex chars from SHA-256 over:

batch_id|fuse_generation|instrument_count|invalid_cert_count|unauthorized_tech_count|sorted instrument_id:severity:out_of_tolerance_count tuples joined by semicolons

Tuple sort is lexicographic ascending.
