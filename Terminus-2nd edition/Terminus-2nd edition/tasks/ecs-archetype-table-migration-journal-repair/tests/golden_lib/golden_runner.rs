use crate::export;
use crate::model::{MigrateExport, WorldSpec};
use crate::staging;
use crate::storage::World;

use super::ledger;

pub fn replay_world(spec: &WorldSpec, seed: &str) -> Result<(), String> {
    let doc = World::migrate_export(spec, seed, false);
    ledger::validate_replay(&doc, spec, seed)?;
    staging::write(staging::DEFAULT_PATH, &doc).map_err(|e| e.to_string())?;
    ledger::write(ledger::DEFAULT_PATH, spec, seed, &doc)
}

pub fn migrate_world(spec: &WorldSpec, seed: &str) -> MigrateExport {
    let ledger_doc = ledger::load(ledger::DEFAULT_PATH).expect("load replay ledger");
    let snap = staging::load(staging::DEFAULT_PATH).expect("load migrate snapshot");
    ledger::assert_migrate_ready(&ledger_doc, spec, seed, &snap).expect("replay ledger invalid");
    export::publish::publish_migrate(staging::DEFAULT_PATH).expect("publish migrate export")
}
