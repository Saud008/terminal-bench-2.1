use crate::cbor::tag24;
use crate::cbor::wire;
use crate::model::types::{DiagnosticTag, PolicyEnvelope, StagingSnapshot};

pub fn encode_staging(snapshot: &StagingSnapshot) -> Vec<u8> {
    let env_inner = wire::encode_map_pairs(&[
        (wire::encode_text("policy"), wire::encode_text(&snapshot.envelope.policy)),
        (wire::encode_text("nonce"), wire::encode_bytes(&snapshot.envelope.nonce)),
    ]);
    let envelope = tag24::wrap_tag24(&env_inner);

    let tag_items: Vec<Vec<u8>> = snapshot
        .diagnostic_tags
        .iter()
        .map(|t| {
            wire::encode_map_pairs(&[
                (wire::encode_text("label"), wire::encode_text(&t.label)),
                (wire::encode_text("tag"), wire::encode_uint(t.tag)),
            ])
        })
        .collect();

    let mut pairs = vec![
        (
            wire::encode_text("version"),
            wire::encode_uint(snapshot.version),
        ),
        (
            wire::encode_text("bundle_id"),
            wire::encode_text(&snapshot.bundle_id),
        ),
        (
            wire::encode_text("diagnostic_tags"),
            wire::encode_array(&tag_items),
        ),
        (wire::encode_text("envelope"), envelope),
    ];
    pairs.sort_by(|a, b| map_key_name(&a.0).cmp(&map_key_name(&b.0)));
    wire::encode_map_pairs(&pairs)
}

fn map_key_name(encoded_key: &[u8]) -> String {
    let mut pos = 0;
    wire::decode_text(encoded_key, &mut pos).unwrap_or_default()
}

pub fn snapshot_from_bundle(
    bundle_id: &str,
    tags: &[DiagnosticTag],
    envelope: &PolicyEnvelope,
) -> StagingSnapshot {
    StagingSnapshot {
        bundle_id: bundle_id.to_string(),
        diagnostic_tags: tags.to_vec(),
        envelope: envelope.clone(),
        version: 1,
    }
}
