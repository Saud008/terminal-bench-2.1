use crate::wx_bundle_read::ManifestDoc;

pub fn wx_anchor_fold(doc: &ManifestDoc) -> bool {
    doc.base_model_hash == doc.expected_base_model_hash
}
