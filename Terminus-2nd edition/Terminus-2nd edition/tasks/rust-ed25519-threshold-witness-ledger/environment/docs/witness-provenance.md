# Witness provenance

Each witness row may reference prior_witness_id pointing to another witness in the same staging snapshot.

The root witness uses prior_witness_id null or the literal none.

A witness provenance_ok when:

- prior is none and the witness is allowed as a chain root, or
- prior names an existing witness_id in staging and that prior witness has a lower epoch than the current witness

Cycles, missing prior ids, or prior epochs greater than or equal to the current epoch fail provenance.

verify quorum sets provenance_ok false on the overall result when any witness row fails provenance validation.
