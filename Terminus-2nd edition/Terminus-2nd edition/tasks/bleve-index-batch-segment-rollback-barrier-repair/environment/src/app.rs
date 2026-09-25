use crate::batch::writer::ingest_batch;
use crate::errors::BleveError;
use crate::export::stage::export_index;
use std::path::Path;

pub fn run_ingest(index: &str, batch_path: &Path) -> Result<(), BleveError> {
    ingest_batch(index, batch_path)
}

pub fn run_export(index: &str, output_path: &Path) -> Result<(), BleveError> {
    export_index(index, output_path)
}
