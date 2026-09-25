use sha2::{Digest, Sha256};

pub fn build_provenance_chain(
    calibration_ids: &[String],
    experiment_id: &str,
    matrix_id: &str,
) -> Vec<String> {
    let mut chain: Vec<String> = calibration_ids.to_vec();
    chain.push(experiment_id.to_string());
    chain.push(matrix_id.to_string());
    chain
}

pub fn provenance_digest(chain: &[String]) -> String {
    let bytes = serde_json::to_vec(chain).unwrap_or_default();
    hex::encode(Sha256::digest(bytes))
}
