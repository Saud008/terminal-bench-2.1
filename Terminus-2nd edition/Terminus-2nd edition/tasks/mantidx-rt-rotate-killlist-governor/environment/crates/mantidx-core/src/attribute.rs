use crate::model::AttributeAudit;
use crate::store::{is_killed, open_db, update_price};
use std::fs;
use std::path::Path;

fn attribute_audit_path(state: &Path) -> std::path::PathBuf {
    state.join("attribute-audit.json")
}

pub fn save_attribute_audit(state: &Path, audit: &AttributeAudit) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(audit).map_err(|e| e.to_string())?;
    fs::write(attribute_audit_path(state), raw).map_err(|e| e.to_string())
}

pub fn run_update_attr(state: &Path, db: &Path, doc_id: i64, price: i64) -> Result<AttributeAudit, String> {
    let conn = open_db(db).map_err(|e| e.to_string())?;
    let killed = is_killed(&conn, doc_id).map_err(|e| e.to_string())?;
    update_price(&conn, doc_id, price).map_err(|e| e.to_string())?;
    let audit = AttributeAudit {
        doc_id,
        price,
        rejected_killed: killed,
    };
    save_attribute_audit(state, &audit)?;
    Ok(audit)
}
