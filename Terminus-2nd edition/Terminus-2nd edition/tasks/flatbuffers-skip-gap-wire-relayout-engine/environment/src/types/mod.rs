#[derive(Clone, Debug)]
pub struct GapSpan {
    pub start: u32,
    pub length: u32,
}

#[derive(Clone, Debug)]
pub struct RootRecord {
    pub table_off: u32,
    pub vtable_off: u32,
    pub vtable_len: u16,
    pub object_size: u16,
    pub slots: Vec<u32>,
}

#[derive(Clone, Debug)]
pub struct WireEntry {
    pub name: String,
    pub wire: Vec<u8>,
    pub roots: Vec<RootRecord>,
    pub gaps: Vec<GapSpan>,
}

#[derive(Clone, Debug)]
pub struct LedgerFile {
    pub ingest_seq: u32,
    pub entries: Vec<WireEntry>,
}

#[derive(Clone, Debug)]
pub struct VtableHeader {
    pub vtable_len: u16,
    pub object_size: u16,
}

#[derive(Clone, Debug)]
pub struct RootDiscovery {
    pub table_off: u32,
    pub vtable_off: u32,
}
