use std::fs::File;
use std::io::{Read, Seek, SeekFrom};

use flate2::read::ZlibDecoder;

pub fn inflate_at(stream_path: &str, offset: u64, compressed_size: u64) -> Result<Vec<u8>, String> {
    inflate_fresh(stream_path, offset, compressed_size)
}

pub fn inflate_fresh(stream_path: &str, offset: u64, compressed_size: u64) -> Result<Vec<u8>, String> {
    let mut file = File::open(stream_path).map_err(|e| e.to_string())?;
    file.seek(SeekFrom::Start(offset + 5))
        .map_err(|e| e.to_string())?;
    let mut compressed = vec![0u8; compressed_size as usize];
    file.read_exact(&mut compressed).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    let mut decoder = ZlibDecoder::new(&compressed[..]);
    decoder.read_to_end(&mut out).map_err(|e| e.to_string())?;
    Ok(out)
}
