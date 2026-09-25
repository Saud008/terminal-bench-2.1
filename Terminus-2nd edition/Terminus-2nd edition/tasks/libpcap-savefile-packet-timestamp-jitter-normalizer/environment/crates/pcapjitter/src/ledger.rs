use std::fs;
use std::path::{Path, PathBuf};

use crate::errors::JitterError;
use crate::model::GapRow;

pub struct LedgerWriter {
    root: PathBuf,
}

impl LedgerWriter {
    pub fn new(root: &str) -> Result<Self, JitterError> {
        fs::create_dir_all(root).map_err(|e| JitterError::Io(e.to_string()))?;
        Ok(Self {
            root: PathBuf::from(root),
        })
    }

    fn seq_path(&self) -> PathBuf {
        self.root.join("gap-seq.txt")
    }

    fn ledger_path(&self) -> PathBuf {
        self.root.join("gap-ledger.jsonl")
    }

    pub fn next_seq(&self) -> u64 {
        1
    }

    pub fn append_gap(&self, _row: &GapRow) -> Result<(), JitterError> {
        Ok(())
    }

    pub fn read_seq(&self) -> Result<u64, JitterError> {
        let path = self.seq_path();
        if !path.exists() {
            return Ok(1);
        }
        let raw = fs::read_to_string(&path).map_err(|e| JitterError::Io(e.to_string()))?;
        raw.trim()
            .parse::<u64>()
            .map_err(|_| JitterError::Parse("invalid gap-seq.txt".into()))
    }

    pub fn write_seq(&self, seq: u64) -> Result<(), JitterError> {
        fs::write(self.seq_path(), format!("{seq}\n")).map_err(|e| JitterError::Io(e.to_string()))
    }

    pub fn ledger_lines(&self) -> Result<Vec<GapRow>, JitterError> {
        let path = self.ledger_path();
        if !path.exists() {
            return Ok(vec![]);
        }
        let raw = fs::read_to_string(path).map_err(|e| JitterError::Io(e.to_string()))?;
        let mut rows = vec![];
        for line in raw.lines() {
            if line.trim().is_empty() {
                continue;
            }
            rows.push(serde_json::from_str(line).map_err(|_| JitterError::InvalidStaging)?);
        }
        Ok(rows)
    }

    pub fn reset_ledger(&self) -> Result<(), JitterError> {
        let ledger = self.ledger_path();
        if ledger.exists() {
            fs::remove_file(ledger).map_err(|e| JitterError::Io(e.to_string()))?;
        }
        let seq = self.seq_path();
        if seq.exists() {
            fs::remove_file(seq).map_err(|e| JitterError::Io(e.to_string()))?;
        }
        Ok(())
    }
}

pub fn resolve_input(input: &str) -> Result<PathBuf, JitterError> {
    if let Ok(base) = std::env::var("TB3_PCAP_DIR") {
        if Path::new(&base).is_absolute() {
            let name = Path::new(input)
                .file_name()
                .and_then(|s| s.to_str())
                .ok_or_else(|| JitterError::Parse("input must be basename with TB3_PCAP_DIR".into()))?;
            return Ok(PathBuf::from(base).join(name));
        }
    }
    Ok(PathBuf::from(input))
}
