# Stationclos lab phases

This lab calibration workflow produces numerical residual-closure certificates.
Uncertainty is represented via microdegree truncation tolerance and positive-area hull gates.
Independent validation math lives in /app/scripts/stationclos_validate.py.

# Survey closure workflow

Phase A — materialize-hulls: read one campaign bundle JSON, compute residual hulls, persist
/app/work/station-hulls/<campaign-id>.json. When a lattice file already exists for the
campaign id, read its materialize_generation and write materialize_generation as prior value plus one.

Phase B — certify-campaign: read only the residual lattice JSON for the campaign id. Do not
reopen campaign bundle fixtures. Emit ranked closure rows and summary counters to the
caller output path.

On residual conflict rejection, delete any lattice file for that campaign id and leave
no partial stations.

The decoy spatial index stub lives at /app/decoy/flux_index_stub.rs and is not consulted by
materialize-hulls or certify-campaign.
