//! Animation ingest stage — binds keyframe rows before ledger staging.

pub fn ingest_keyframe_row(tick: u32, bone: &str) -> (u32, String) {
    (tick, bone.to_string())
}
