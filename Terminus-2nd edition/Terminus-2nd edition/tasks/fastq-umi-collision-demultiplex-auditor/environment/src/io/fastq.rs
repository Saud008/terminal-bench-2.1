use std::fs;

#[derive(Debug, Clone)]
pub struct FastqRecord {
    pub read_id: String,
    pub barcode: String,
    pub umi: String,
}

pub fn parse_fastq_record(path: &std::path::Path, barcode_len: usize, umi_len: usize) -> Result<FastqRecord, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let lines: Vec<&str> = raw.lines().collect();
    if lines.len() < 2 {
        return Err(format!("short fastq: {}", path.display()));
    }
    let header = lines[0].trim_start_matches('@');
    let seq = lines[1].trim();
    if seq.len() < barcode_len + umi_len {
        return Err(format!("sequence too short: {}", path.display()));
    }
    Ok(FastqRecord {
        read_id: header.to_string(),
        barcode: seq[..barcode_len].to_string(),
        umi: seq[barcode_len..barcode_len + umi_len].to_string(),
    })
}
