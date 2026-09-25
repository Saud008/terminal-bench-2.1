use crate::adler;
use serde_json::json;
use std::fs;
use std::path::Path;

pub struct Report {
    pub input_path: String,
    pub output_path: String,
    pub uncompressed_len: usize,
    pub adler32: u32,
    pub computed_adler32: u32,
    pub block_count: usize,
    pub ok: bool,
}

pub fn write_outputs(
    input_path: &str,
    output_path: &str,
    report_path: &str,
    data: &[u8],
    expected_adler: u32,
    block_count: usize,
) -> Result<Report, String> {
    if let Some(parent) = Path::new(output_path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    if let Some(parent) = Path::new(report_path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(output_path, data).map_err(|e| e.to_string())?;
    let computed = adler::adler32(data);
    let ok = computed == expected_adler;
    let report = Report {
        input_path: input_path.to_string(),
        output_path: output_path.to_string(),
        uncompressed_len: data.len(),
        adler32: expected_adler,
        computed_adler32: computed,
        block_count,
        ok,
    };
    let body = json!({
        "input_path": report.input_path,
        "output_path": report.output_path,
        "uncompressed_len": report.uncompressed_len,
        "adler32": report.adler32,
        "computed_adler32": report.computed_adler32,
        "block_count": report.block_count,
        "ok": report.ok,
    });
    fs::write(report_path, serde_json::to_string_pretty(&body).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    Ok(report)
}
