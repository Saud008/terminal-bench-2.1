use crate::crypto::revocation;
use crate::types::{StagingDoc, WitnessOutcome, WitnessRow};

pub fn evaluate_quorum(
    staging: &StagingDoc,
    epoch: u64,
    outcomes: &[WitnessOutcome],
) -> (bool, u32) {
    let threshold = staging.policy.quorum.threshold;
    let mut valid = 0u32;
    for o in outcomes {
        if o.counts_toward_quorum {
            valid += 1;
        }
    }
    let _ = epoch;
    (valid >= threshold, valid)
}

pub fn build_outcomes(staging: &StagingDoc, epoch: u64) -> Vec<WitnessOutcome> {
    staging
        .witnesses
        .iter()
        .map(|w| score_witness(staging, w, epoch))
        .collect()
}

fn score_witness(staging: &StagingDoc, witness: &WitnessRow, epoch: u64) -> WitnessOutcome {
    let key = staging.keys.get(&witness.signer_keyid);
    let signature_ok = key
        .map(|k| crate::crypto::ed25519_verify::verify_witness_signature(witness, k))
        .unwrap_or(false);
    let revoked_signer = revocation::is_revoked(&witness.signer_keyid, &staging.revocations, epoch);
    let provenance_ok = crate::ledger::provenance::chain_valid(&staging.witnesses, witness);
    let counts_toward_quorum = signature_ok && provenance_ok;
    WitnessOutcome {
        witness_id: witness.witness_id.clone(),
        signature_ok,
        provenance_ok,
        revoked_signer,
        counts_toward_quorum,
    }
}
