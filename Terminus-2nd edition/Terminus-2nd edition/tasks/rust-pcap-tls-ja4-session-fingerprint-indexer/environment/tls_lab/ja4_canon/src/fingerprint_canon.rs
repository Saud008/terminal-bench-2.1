use sha2::{Digest, Sha256};

#[derive(Debug, Clone)]
pub struct HandshakeView {
    pub tls_version: u16,
    pub cipher_suites: Vec<u16>,
    pub extensions: Vec<u16>,
    pub alpn: String,
}

fn extension_hash(exts: &[u16]) -> String {
    let mut h = Sha256::new();
    for e in exts {
        h.update(e.to_be_bytes());
    }
    let digest = h.finalize();
    let hex = digest.iter().map(|b| format!("{b:02x}")).collect::<String>();
    hex.chars().take(12).collect()
}

pub fn seal_handshake_tag(h: &HandshakeView) -> String {
    let mut ciphers = h.cipher_suites.clone();
    ciphers.sort();
    let cipher_count = format!("{:02x}", ciphers.len().min(255));
    let ver = format!("{:02x}", h.tls_version & 0xFF);
    // extension list hashed in capture order
    let ext_hash = extension_hash(&h.extensions);
    let alpn = if h.alpn.is_empty() {
        "00".into()
    } else {
        h.alpn.chars().take(2).collect::<String>()
    };
    format!("t{ver}d{cipher_count}h{ext_hash}_{alpn}")
}
