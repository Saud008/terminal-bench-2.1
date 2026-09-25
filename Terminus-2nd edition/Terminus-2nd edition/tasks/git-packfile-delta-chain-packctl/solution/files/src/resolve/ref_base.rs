use crate::types::{allowed_delta_base, PackStage, StageObject};

pub fn lookup_ref_base<'a>(stage: &'a PackStage, base_id: &str) -> Result<&'a StageObject, String> {
    let base = stage
        .objects
        .iter()
        .find(|o| o.id == base_id)
        .ok_or_else(|| format!("missing base {base_id}"))?;
    if !allowed_delta_base(&base.kind) {
        return Err(format!("invalid delta base kind {}", base.kind));
    }
    Ok(base)
}
