use std::fs;
use std::path::Path;

use crate::ledger::{bump_ingest_seq, from_parsed, save_ledger};
use crate::parse::parse_cwrc;

pub fn load_directory(dir: &str, ledger_path: &str) -> Result<(), String> {
    let path = Path::new(dir);
    if !path.is_dir() {
        return Err(format!("missing components dir {dir}"));
    }
    let mut names: Vec<String> = fs::read_dir(path)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .filter(|n| n.ends_with(".cwasm"))
        .collect();
    names.sort();
    let mut parsed = Vec::new();
    for name in names {
        let full = path.join(&name);
        let raw = fs::read(&full).map_err(|e| e.to_string())?;
        parsed.push(parse_cwrc(&name, &raw)?);
    }
    let seq = bump_ingest_seq(ledger_path);
    let ledger = from_parsed(seq, parsed);
    save_ledger(ledger_path, &ledger)
}
