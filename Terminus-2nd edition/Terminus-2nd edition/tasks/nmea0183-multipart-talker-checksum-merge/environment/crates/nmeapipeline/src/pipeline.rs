use std::fs;
use std::path::Path;

use crate::context::rmc;
use crate::export::{staging, writer};
use crate::merge::compose;
use crate::model::{MergeSnapshot, RejectedLine};
use crate::parse::fields;
use crate::session::pending::PendingStore;
use crate::session::store::SessionState;

pub fn run_merge(input: &Path, output: &Path, state_path: Option<&Path>) -> Result<(), String> {
    let text = fs::read_to_string(input).map_err(|e| e.to_string())?;
    let use_session = state_path.is_some();
    let mut session = if let Some(p) = state_path {
        if p.exists() {
            let t = fs::read_to_string(p).map_err(|e| e.to_string())?;
            serde_json::from_str(&t).unwrap_or_default()
        } else {
            SessionState::default()
        }
    } else {
        SessionState::default()
    };

    let prev_date = session.rmc_date.clone();
    let mut pending = PendingStore::from_groups(session.pending.clone());
    let mut sentences = Vec::new();
    let mut rejected = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        match fields::parse_line(line) {
            Ok(s) => {
                let date_before = session.rmc_date.clone();
                if rmc::update_rmc_context(&s, &mut session.rmc_date, &mut session.rmc_time) {
                    if use_session {
                        if let (Some(old), Some(new)) = (date_before.as_ref(), session.rmc_date.as_ref()) {
                            if old != new {
                                pending.clear_all();
                            }
                        } else if prev_date.is_some()
                            && session.rmc_date.is_some()
                            && prev_date.as_ref() != session.rmc_date.as_ref()
                        {
                            pending.clear_all();
                        }
                    }
                }
                sentences.push(s);
            }
            Err(reason) => rejected.push(RejectedLine {
                line: line.to_string(),
                reason,
            }),
        }
    }

    let mut result = compose::compose_stream(
        sentences,
        pending,
        session.rmc_date.clone(),
        session.rmc_time.clone(),
        use_session,
    );
    result.rejected.extend(rejected);
    session.rmc_date = result.rmc_date.clone();
    session.rmc_time = result.rmc_time.clone();

    // Attach UTC onto multipart groups using context
    for g in &mut result.groups {
        if g.utc_iso.is_none() {
            // leave None for multipart unless we have time in payload — skip
        }
    }

    let mut snapshot = MergeSnapshot {
        groups: result.groups,
        rejected: result.rejected,
        snapshot_digest: String::new(),
    };
    writer::finalize_digest(&mut snapshot);
    let snap_path = Path::new("/app/state/merge-snapshot.json");
    staging::write_snapshot(snap_path, &snapshot)?;
    staging::publish_export(snap_path, output)?;

    if let Some(p) = state_path {
        // Only persist buckets that include fragment one
        let mut groups = result.pending.into_groups();
        groups.retain(|g| g.fragments.iter().any(|f| f.fields.get(1).map(|v| v == "1").unwrap_or(false)));
        // BROKEN env pending may still stash orphans — filter on save in pipeline for session file contract when fixed pending is applied
        session.pending = groups;
        if let Some(parent) = p.parent() {
            fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        let t = serde_json::to_string_pretty(&session).map_err(|e| e.to_string())?;
        fs::write(p, t).map_err(|e| e.to_string())?;
    }
    Ok(())
}
