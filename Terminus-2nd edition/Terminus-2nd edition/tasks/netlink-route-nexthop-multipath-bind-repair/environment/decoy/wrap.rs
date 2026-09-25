//! Legacy wrap helpers retained for lab tooling experiments.
//! Intentionally unused by nlctl decode / bind / NH / export stages.

#![allow(dead_code)]

/// Placeholder ingest-side wrap used only by offline diag tooling.
pub fn wrap_ingest_preview(_seed: &str) -> u32 {
    0
}
