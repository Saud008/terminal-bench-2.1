use anomaly_count::count_anomalies;
use capsule_io::{read_capsule_dir, CapsuleFrame, SessionKey};
use retrans_dedupe::dedupe_frames;
use role_detect::endpoint_label_table;
use serde::{Deserialize, Serialize};
use session_quad::format_session_id;
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StagedSession {
    pub session_id: String,
    pub role_map: std::collections::BTreeMap<String, String>,
    pub handshake_bytes: Vec<u8>,
    pub frame_count: u32,
    pub unique_frames: u32,
    pub anomalies: anomaly_count::AnomalyCounters,
}

pub fn persist_capsule_ledger(capsule_dir: &Path, ledger_path: &Path) -> Result<(), String> {
    let frames = read_capsule_dir(capsule_dir).map_err(|_| "capsule read failed".to_string())?;
    let deduped = dedupe_frames(&frames);
    let sessions: BTreeSet<[u8; 8]> = deduped.iter().map(|f| f.session.quad).collect();
    let mut staged_rows = Vec::new();
    for quad in sessions {
        let sk = SessionKey { quad };
        let raw_sess: Vec<CapsuleFrame> = frames.iter().filter(|f| f.session.quad == quad).cloned().collect();
        let sess_frames: Vec<CapsuleFrame> = deduped.iter().filter(|f| f.session.quad == quad).cloned().collect();
        let handshake = collect_handshake_bytes(&sess_frames);
        let roles = endpoint_label_table(&frames, &sk);
        let anomalies = count_anomalies(&raw_sess);
        staged_rows.push(StagedSession {
            session_id: format_session_id(&quad),
            role_map: roles,
            handshake_bytes: handshake,
            frame_count: raw_sess.len() as u32,
            unique_frames: sess_frames.len() as u32,
            anomalies,
        });
    }
    staged_rows.sort_by(|a, b| a.session_id.cmp(&b.session_id));
    let lines: Vec<String> = staged_rows
        .into_iter()
        .map(|s| serde_json::to_string(&s).map_err(|e| e.to_string()))
        .collect::<Result<_, _>>()?;
    fs::write(ledger_path, format!("{}
", lines.join("
"))).map_err(|e| e.to_string())
}

fn collect_handshake_bytes(frames: &[CapsuleFrame]) -> Vec<u8> {
    let mut buf = Vec::new();
    for f in frames {
        buf.extend_from_slice(&f.tls_payload);
    }
    buf
}

pub fn read_ledger(path: &Path) -> Result<Vec<StagedSession>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    raw.lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| serde_json::from_str(l).map_err(|e| e.to_string()))
        .collect()
}
