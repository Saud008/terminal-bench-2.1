use capsule_io::CapsuleFrame;

#[derive(Debug, Clone)]
pub struct TlsRecord {
    pub content_type: u8,
    pub version: u16,
    pub body: Vec<u8>,
}

pub fn reassemble_records(frames: &[CapsuleFrame]) -> Vec<TlsRecord> {
    let mut records = Vec::new();
    let mut pending: Vec<u8> = Vec::new();
    for frame in frames {
        pending.extend_from_slice(&frame.tls_payload);
        while pending.len() >= 5 {
            let ctype = pending[0];
            let ver = u16::from_be_bytes([pending[1], pending[2]]);
            let len = u16::from_be_bytes([pending[3], pending[4]]) as usize;
            if pending.len() < 5 + len {
                break;
            }
            let body = pending[5..5 + len].to_vec();
            pending = pending[5 + len..].to_vec();
            records.push(TlsRecord {
                content_type: ctype,
                version: ver,
                body,
            });
        }
    }
    records
}
