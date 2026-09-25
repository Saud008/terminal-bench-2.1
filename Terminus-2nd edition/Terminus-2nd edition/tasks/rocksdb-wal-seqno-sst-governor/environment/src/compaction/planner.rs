use crate::types::SstFileRow;

/// Select SST catalog entries for compaction planning.
pub fn select_sst_files(files: &[SstFileRow], _watermark: u64) -> Vec<String> {
    let mut sorted: Vec<&SstFileRow> = files.iter().collect();
    sorted.sort_by(|a, b| b.size_bytes.cmp(&a.size_bytes));
    sorted.into_iter().map(|f| f.file_id.clone()).collect()
}
