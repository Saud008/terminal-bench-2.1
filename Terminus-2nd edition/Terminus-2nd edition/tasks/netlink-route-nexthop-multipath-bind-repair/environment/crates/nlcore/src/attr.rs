pub const RTA_OIF: u16 = 4;
pub const RTA_GATEWAY: u16 = 5;
pub const RTA_PRIORITY: u16 = 6;
pub const RTA_MULTIPATH: u16 = 8;
pub const RTA_TABLE: u16 = 15;
pub const RTA_METRICS: u16 = 39;
pub const RTA_NH_ID: u16 = 52;

pub const AF_INET: u8 = 2;
pub const AF_INET6: u8 = 10;

pub const RTAX_MTU: u16 = 2;
pub const RTAX_ADVMSS: u16 = 5;

pub fn metric_name(t: u16) -> Option<&'static str> {
    match t {
        RTAX_MTU => Some("mtu"),
        RTAX_ADVMSS => Some("advmss"),
        _ => None,
    }
}
