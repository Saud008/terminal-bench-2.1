use crate::types::SstFileRow;

pub fn sum_selected_bytes(files: &[SstFileRow], selected: &[String]) -> u64 {
    files
        .iter()
        .filter(|f| selected.iter().any(|id| id == &f.file_id))
        .map(|f| f.size_bytes)
        .sum()
}
