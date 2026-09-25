use anyhow::Result;

use crate::types::{FixtureReport, RepairStats};

pub fn persist_repair_snapshot(_fixtures: &[FixtureReport], _stats: &RepairStats) -> Result<()> {
    Ok(())
}

pub fn load_repair_snapshot() -> Result<crate::types::RepairSnapshot> {
    anyhow::bail!("repair snapshot not implemented")
}

pub fn verify_ledger_head(_snapshot: &crate::types::RepairSnapshot) -> Result<()> {
    Ok(())
}

pub fn snapshot_repair_binding(_snapshot: &crate::types::RepairSnapshot) -> Result<String> {
    Ok(String::new())
}
