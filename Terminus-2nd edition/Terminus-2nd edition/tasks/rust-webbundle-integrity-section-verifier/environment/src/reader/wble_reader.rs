#[derive(Debug, Clone)]
pub struct WbleBundle {
    pub bundle_id: String,
    pub primary_url: String,
    pub scopes: Vec<String>,
    pub allowed_mimes: Vec<String>,
    pub exchanges: Vec<ExchangeRecord>,
    pub integrity_hashes: Vec<[u8; 32]>,
}

#[derive(Debug, Clone)]
pub struct ExchangeRecord {
    pub variant_id: u32,
    pub url: String,
    pub status: u16,
    pub headers: Vec<(String, String)>,
    pub body: Vec<u8>,
}

use std::fs;
use std::path::Path;

#[derive(Debug)]
pub struct BundleError;

const MAGIC: &[u8; 4] = b"WBLE";
const IHSH: &[u8; 4] = b"IHSH";

pub fn read_bundle_dir(dir: &Path) -> Result<Vec<WbleBundle>, BundleError> {
    let mut bundles = Vec::new();
    let mut paths: Vec<_> = fs::read_dir(dir).map_err(|_| BundleError)?.filter_map(|e| e.ok()).collect();
    paths.sort_by_key(|e| e.file_name());
    for entry in paths {
        let p = entry.path();
        if p.extension().and_then(|s| s.to_str()) != Some("wble") {
            continue;
        }
        bundles.push(parse_bundle(&fs::read(&p).map_err(|_| BundleError)?, &p)?);
    }
    bundles.sort_by(|a, b| a.bundle_id.cmp(&b.bundle_id));
    Ok(bundles)
}

fn parse_bundle(bytes: &[u8], path: &Path) -> Result<WbleBundle, BundleError> {
    if bytes.len() < 8 || &bytes[0..4] != MAGIC {
        return Err(BundleError);
    }
    let version = u16::from_le_bytes(bytes[4..6].try_into().map_err(|_| BundleError)?);
    if version != 1 {
        return Err(BundleError);
    }
    let mut off = 6usize;
    let primary_url = read_str(bytes, &mut off)?;
    let scope_count = u16::from_le_bytes(bytes[off..off + 2].try_into().map_err(|_| BundleError)?) as usize;
    off += 2;
    let mut scopes = Vec::new();
    for _ in 0..scope_count {
        scopes.push(read_str(bytes, &mut off)?);
    }
    let mime_count = u16::from_le_bytes(bytes[off..off + 2].try_into().map_err(|_| BundleError)?) as usize;
    off += 2;
    let mut allowed_mimes = Vec::new();
    for _ in 0..mime_count {
        allowed_mimes.push(read_str(bytes, &mut off)?);
    }
    let ex_count = u32::from_be_bytes(bytes[off..off + 4].try_into().map_err(|_| BundleError)?) as usize;
    off += 4;
    let mut exchanges = Vec::new();
    for _ in 0..ex_count {
        if off + 8 > bytes.len() {
            return Err(BundleError);
        }
        let variant_id = u32::from_le_bytes(bytes[off..off + 4].try_into().map_err(|_| BundleError)?);
        off += 4;
        let url = read_str(bytes, &mut off)?;
        let status = u16::from_le_bytes(bytes[off..off + 2].try_into().map_err(|_| BundleError)?);
        off += 2;
        let hdr_count = u16::from_le_bytes(bytes[off..off + 2].try_into().map_err(|_| BundleError)?) as usize;
        off += 2;
        let mut headers = Vec::new();
        for _ in 0..hdr_count {
            let name = read_str(bytes, &mut off)?;
            let value = read_str(bytes, &mut off)?;
            headers.push((name, value));
        }
        let body_len = u32::from_le_bytes(bytes[off..off + 4].try_into().map_err(|_| BundleError)?) as usize;
        off += 4;
        if off + body_len > bytes.len() {
            return Err(BundleError);
        }
        let body = bytes[off..off + body_len].to_vec();
        off += body_len;
        exchanges.push(ExchangeRecord {
            variant_id,
            url,
            status,
            headers,
            body,
        });
    }
    let mut integrity_hashes = Vec::new();
    if off + 4 <= bytes.len() && &bytes[off..off + 4] == IHSH {
        off += 4;
        let hash_count = u32::from_le_bytes(bytes[off..off + 4].try_into().map_err(|_| BundleError)?) as usize;
        off += 4;
        for _ in 0..hash_count {
            if off + 32 > bytes.len() {
                return Err(BundleError);
            }
            let mut h = [0u8; 32];
            h.copy_from_slice(&bytes[off..off + 32]);
            integrity_hashes.push(h);
            off += 32;
        }
    }
    let bundle_id = path.file_stem().and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    Ok(WbleBundle {
        bundle_id,
        primary_url,
        scopes,
        allowed_mimes,
        exchanges,
        integrity_hashes,
    })
}

fn read_str(bytes: &[u8], off: &mut usize) -> Result<String, BundleError> {
    if *off + 2 > bytes.len() {
        return Err(BundleError);
    }
    let len = u16::from_le_bytes(bytes[*off..*off + 2].try_into().map_err(|_| BundleError)?) as usize;
    *off += 2;
    if *off + len > bytes.len() {
        return Err(BundleError);
    }
    let s = std::str::from_utf8(&bytes[*off..*off + len]).map_err(|_| BundleError)?.to_string();
    *off += len;
    Ok(s)
}
