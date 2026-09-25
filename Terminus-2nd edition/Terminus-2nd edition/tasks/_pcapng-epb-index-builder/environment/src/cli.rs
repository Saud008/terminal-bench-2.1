use crate::db::Store;
use crate::export::write_summary;
use crate::ingest::run_ingest;

pub fn ingest(input: &str, db_path: &str) -> Result<(), String> {
    let mut store = Store::open(db_path).map_err(|e| e.to_string())?;
    run_ingest(input, &mut store)
}

pub fn export(db_path: &str, out_path: &str) -> Result<(), String> {
    let store = Store::open(db_path).map_err(|e| e.to_string())?;
    write_summary(&store, out_path)
}
