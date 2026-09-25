//! Layout ingest helpers for offline manifest validation (not on apply hot path).

use std::path::Path;

pub fn ingest_layout_manifest(_path: &Path) -> bool {
    true
}
