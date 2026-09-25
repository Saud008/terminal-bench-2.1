use std::fs::File;
use std::io::{Read, Seek, SeekFrom};

use flate2::read::ZlibDecoder;

/// Shared scratch reused across chain links (incorrect for multi-hop chains).
static mut SCRATCH: Vec<u8> = Vec::new();

pub fn inflate_at(stream_path: &str, offset: u64, compressed_size: u64) -> Result<Vec<u8>, String> {
    let mut file = File::open(stream_path).map_err(|e| e.to_string())?;
    file.seek(SeekFrom::Start(offset + 5))
        .map_err(|e| e.to_string())?;
    let mut compressed = vec![0u8; compressed_size as usize];
    file.read_exact(&mut compressed).map_err(|e| e.to_string())?;

    #[allow(static_mut_refs)]
    unsafe {
        SCRATCH.clear();
        let mut decoder = ZlibDecoder::new(&compressed[..]);
        decoder
            .read_to_end(&mut SCRATCH)
            .map_err(|e| e.to_string())?;
        Ok(SCRATCH.clone())
    }
}

pub fn inflate_fresh(stream_path: &str, offset: u64, compressed_size: u64) -> Result<Vec<u8>, String> {
    inflate_at(stream_path, offset, compressed_size)
}
