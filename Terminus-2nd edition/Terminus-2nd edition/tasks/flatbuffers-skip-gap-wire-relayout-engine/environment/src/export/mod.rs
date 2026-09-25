pub mod seal;

use crate::relayout;
use crate::staging;

pub fn relayout_export(ledger_path: &str, out_wire: &str, seal_path: &str) -> Result<(), String> {
    let ledger = staging::load_ledger(ledger_path)?;
    let mut relaid = relayout::relayout_from_ledger(&ledger)?;
    seal::write_outputs(&mut relaid, &ledger, out_wire, seal_path)
}
