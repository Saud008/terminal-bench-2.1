use crate::yard_model::{Config, LotoTicket, YardSnapshot};
use sha2::{Digest, Sha256};
use std::fs;

pub fn ticket_id(seed: &str, scenario: &str, load_seq: u64) -> String {
    let body = format!("{seed}:{scenario}:{load_seq}");
    let digest = Sha256::digest(body.as_bytes());
    format!("loto-{}", hex::encode(&digest[..6]))
}

pub fn run_stage(cfg: &Config, seed: &str, scenario: &str) -> Result<(), String> {
    let snap = crate::seq_anchor::read_snapshot(&cfg.yard_cache_path)?;
    let ticket = LotoTicket {
        ticket_id: ticket_id(seed, scenario, snap.load_seq),
        seed: seed.to_string(),
        scenario: scenario.to_string(),
        load_seq: snap.load_seq,
        active: true,
    };
    write_ticket(&cfg.loto_ticket_path, &ticket)
}

pub fn read_ticket(path: &str) -> Result<LotoTicket, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn write_ticket(path: &str, ticket: &LotoTicket) -> Result<(), String> {
    if let Some(parent) = std::path::Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(ticket).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

pub fn validate_ticket(ticket: &LotoTicket, snap: &YardSnapshot) -> Result<(), String> {
    if ticket.load_seq != snap.load_seq {
        return Err("loto ticket stale".into());
    }
    Ok(())
}
