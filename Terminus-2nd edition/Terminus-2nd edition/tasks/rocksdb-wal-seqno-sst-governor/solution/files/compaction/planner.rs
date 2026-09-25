use crate::types::SstFileRow;

pub fn select_sst_files(files: &[SstFileRow], watermark: u64) -> Vec<String> {
    let mut eligible: Vec<&SstFileRow> = files
        .iter()
        .filter(|f| f.max_seqno <= watermark)
        .collect();
    eligible.sort_by(|a, b| a.file_id.cmp(&b.file_id));
    eligible.into_iter().map(|f| f.file_id.clone()).collect()
}
