#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SessionKey {
    pub quad: [u8; 8],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Client,
    Server,
}

#[derive(Debug, Clone)]
pub struct CapsuleFrame {
    pub session: SessionKey,
    pub seq: u32,
    pub direction: Direction,
    pub tls_payload: Vec<u8>,
    pub is_retransmit: bool,
}
