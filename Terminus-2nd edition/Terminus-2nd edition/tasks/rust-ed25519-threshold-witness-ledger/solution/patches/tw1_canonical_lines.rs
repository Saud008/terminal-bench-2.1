pub fn canonical_message(
    release_id: &str,
    artifact_digest: &str,
    epoch: u64,
    prior_witness_id: Option<&str>,
) -> Vec<u8> {
    let prior = prior_witness_id.unwrap_or("none");
    format!(
        "TW1\nartifact_digest={artifact_digest}\nepoch={epoch}\nprior_witness_id={prior}\nrelease_id={release_id}\n"
    )
    .into_bytes()
}
