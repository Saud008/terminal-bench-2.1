use crate::types::{PackStage, StageObject};

pub fn lookup_ref_base<'a>(stage: &'a PackStage, base_id: &str) -> Result<&'a StageObject, String> {
    stage
        .objects
        .iter()
        .find(|o| o.id == base_id)
        .ok_or_else(|| format!("missing base {base_id}"))
}
