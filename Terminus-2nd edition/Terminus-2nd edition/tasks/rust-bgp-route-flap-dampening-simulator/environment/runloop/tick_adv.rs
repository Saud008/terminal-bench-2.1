use crate::feed_normalize;
use crate::ledger_store;
use crate::lock_store;
use crate::route_model::FlapLedger;
use crate::prefix_steps;
use std::collections::BTreeMap;

pub fn drive_feed(scenario_id: &str, root: &str) -> Result<(), String> {
    let scenario_lock = lock_store::load()?;
    if scenario_lock.scenario_id != scenario_id {
        return Err("lock scenario mismatch".into());
    }
    let events = feed_normalize::load_events_from_root(root, &scenario_lock.feed_relpath)?;
    if events.len() as u64 != scenario_lock.line_count {
        return Err("feed line_count mismatch".into());
    }
    let mut entries = BTreeMap::new();
    for ev in &events {
        prefix_steps::step(&mut entries, &scenario_lock.peer_table, ev);
    }
    let run_id = ledger_store::read_run_id() + 1;
    ledger_store::advance_run_id(run_id)?;
    let ledger = FlapLedger {
        scenario_id: scenario_id.to_string(),
        run_id,
        entries,
    };
    ledger_store::write_ledger(&ledger)
}
