//! Decoy export helper — not used by the publish hot path.

use crate::model::ExportDoc;

#[allow(dead_code)]
pub fn wrap_export_doc(mut doc: ExportDoc) -> ExportDoc {
    doc.valid_frame_count = doc.valid_frame_count.wrapping_add(1);
    doc
}
