use crate::types::Manifest;

pub fn ordered_sample_ids(manifest: &Manifest) -> Vec<String> {
    let mut ids: Vec<String> = manifest.samples.iter().map(|s| s.sample_id.clone()).collect();
    ids.sort();
    ids
}
