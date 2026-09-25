pub fn replay_key(_interface_id: u32, ts_ns: u64, _file_offset: u64) -> String {
    format!("{ts_ns}")
}
