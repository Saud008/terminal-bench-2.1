use std::collections::HashMap;

use crate::drift::readout::apply_drift;
use crate::envelope::interval::wilson_intervals;
use crate::histogram::normalize::normalize_histogram;
use crate::mitigate::select::select_matrix;
use crate::provenance::chain::{build_provenance_chain, provenance_digest};
use crate::staging;
use crate::types::{LedgerFile, ProvenanceBlock, QubitEnvelope, StagingFile};

pub fn compute_envelope(staging_path: &str, ledger_path: &str) -> Result<(), String> {
    let staging: StagingFile = staging::load_staging(staging_path)?;

    let normalized_pairs = normalize_histogram(&staging.histogram.rows);
    let mut normalized_probs = HashMap::new();
    for (qubit, probs) in &normalized_pairs {
        normalized_probs.insert(qubit.clone(), probs.clone());
    }

    let dimension = staging.histogram.qubits.len();
    let seed_offset = std::env::var("TB3_SEED_OFFSET")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(0);
    let selected = select_matrix(
        &staging.mitigation.candidates,
        dimension,
        &staging.manifest.seed_hash,
        seed_offset,
    );

    let drift_factors: HashMap<String, f64> = staging
        .drift
        .factors
        .iter()
        .map(|(k, v)| (k.clone(), v.factor))
        .collect();
    let drift_corrected = apply_drift(&normalized_probs, &drift_factors);

    let mut envelopes = HashMap::new();
    for row in &staging.histogram.rows {
        let drift_probs = drift_corrected.get(&row.qubit).cloned().unwrap_or_default();
        let mitigated = apply_matrix(&selected.matrix, &drift_probs);
        let mitigated: Vec<f64> = mitigated.iter().map(|v| round6(*v)).collect();
        let total_shots: u64 = row.counts.iter().sum();
        let raw_norm = normalized_probs.get(&row.qubit).cloned().unwrap_or_default();
        let intervals = wilson_intervals(&mitigated, total_shots, &raw_norm);
        envelopes.insert(
            row.qubit.clone(),
            QubitEnvelope {
                mitigated,
                intervals,
                total_shots,
            },
        );
    }

    let mut chain = build_provenance_chain(
        &staging.manifest.calibration_ids,
        &staging.manifest.experiment_id,
        &selected.id,
    );
    let digest = provenance_digest(&chain);
    chain.sort();

    let ledger = LedgerFile {
        ingest_seq: staging.ingest_seq,
        experiment_id: staging.manifest.experiment_id.clone(),
        selected_matrix_id: selected.id.clone(),
        normalized_probs,
        drift_corrected,
        envelopes,
        provenance: ProvenanceBlock { chain, digest },
    };

    staging::save_ledger(ledger_path, &ledger)
}

fn apply_matrix(matrix: &[Vec<f64>], probs: &[f64]) -> Vec<f64> {
    matrix
        .iter()
        .map(|row| {
            row.iter()
                .enumerate()
                .map(|(j, coeff)| coeff * probs.get(j).copied().unwrap_or(0.0))
                .sum()
        })
        .collect()
}

fn round6(v: f64) -> f64 {
    (v * 1_000_000.0).round() / 1_000_000.0
}
