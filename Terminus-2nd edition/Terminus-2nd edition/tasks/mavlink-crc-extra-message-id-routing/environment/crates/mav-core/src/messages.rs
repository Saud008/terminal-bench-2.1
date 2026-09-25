pub const MSG_HEARTBEAT: u32 = 0;
pub const MSG_SYS_STATUS: u32 = 1;
pub const MSG_GPS_RAW_INT: u32 = 24;
pub const MSG_EVENT_LOG: u32 = 11000;

pub fn message_name(msg_id: u32) -> &'static str {
    match msg_id {
        MSG_HEARTBEAT => "HEARTBEAT",
        MSG_SYS_STATUS => "SYS_STATUS",
        MSG_GPS_RAW_INT => "GPS_RAW_INT",
        MSG_EVENT_LOG => "EVENT_LOG",
        _ => "UNKNOWN",
    }
}

pub fn crc_extra(msg_id: u32) -> Option<u8> {
    match msg_id {
        MSG_HEARTBEAT => Some(50),
        MSG_SYS_STATUS => Some(124),
        MSG_GPS_RAW_INT => Some(24),
        MSG_EVENT_LOG => Some(195),
        _ => None,
    }
}
