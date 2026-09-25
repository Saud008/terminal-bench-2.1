# Release-approval witness ledger contract

twctl is the host-local release-approval ops desk for witness ledgers (admit -> gate -> seal). It is not a remote signing service and not a generic metadata profiler.

## Witness row lifecycle

Each witness row binds a release_id, artifact_digest, approval round, prior_witness_id, signer_keyid, and TW1 canonical message bytes with an attached signature field. Rows accumulate in tw-approval-stage.json across load calls with replay deduplication by witness_id.

## Quorum state machine

check transitions staging into quorum-verdict.json at the effective verification round. Revocation rounds filter signer_keyid rows before distinct-signer counting. Provenance requires prior witness rounds to be strictly earlier.

## Sealed export state

emit closes the machine: it reads only staging and quorum-verdict, never bundle witness JSON, and writes release-witness-ledger.json with ledger_digest over sorted witness export rows.

## Not a scientific metadata profiler

No dataset catalogs, chunk masks, or HDF5 filters appear in this contract. The ops problem is release-approval admission, quorum gates, and sealed export - not array chunk traversal.
