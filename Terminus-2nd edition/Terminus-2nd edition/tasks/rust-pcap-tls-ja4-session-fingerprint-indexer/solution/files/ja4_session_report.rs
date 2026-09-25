use hello_summary::parse_handshake_view;
use ja4_canon::seal_handshake_tag;
use ledger_store::StagedSession;
use serde::Serialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct SessionRow {
    pub session_id: String,
    pub role_map: std::collections::BTreeMap<String, String>,
    pub ja4: String,
    pub frame_count: u32,
    pub unique_frames: u32,
    pub anomalies: anomaly_count::AnomalyCounters,
}

#[derive(Debug, Serialize)]
pub struct SessionIndex {
    pub sessions: Vec<SessionRow>,
    pub totals: Totals,
}

#[derive(Debug, Serialize)]
pub struct Totals {
    pub session_count: u32,
    pub anomaly_frames: u32,
}

pub fn publish_ledger_report(ledger_path: &Path, out_path: &Path) -> Result<(), String> {
    let staged = ledger_store::read_ledger(ledger_path)?;
    let mut sessions = Vec::new();
    let mut anomaly_frames = 0u32;
    for s in staged {
        let view = parse_handshake_view(&s.handshake_bytes);
        let ja4 = seal_handshake_tag(&view);
        anomaly_frames += s.anomalies.retransmit;
        sessions.push(SessionRow {
            session_id: s.session_id,
            role_map: s.role_map,
            ja4,
            frame_count: s.frame_count,
            unique_frames: s.unique_frames,
            anomalies: s.anomalies,
        });
    }
    sessions.sort_by(|a, b| a.session_id.cmp(&b.session_id));
    let count = sessions.len() as u32;
    let index = SessionIndex {
        sessions,
        totals: Totals {
            session_count: count,
            anomaly_frames,
        },
    };
    let json = serde_json::to_string_pretty(&index).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}
")).map_err(|e| e.to_string())
}

pub use anomaly_count;
