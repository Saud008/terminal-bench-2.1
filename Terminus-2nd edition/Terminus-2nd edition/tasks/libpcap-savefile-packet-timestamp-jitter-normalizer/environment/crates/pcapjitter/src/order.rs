use crate::model::PacketMeta;

pub fn global_sort(packets: &mut [PacketMeta]) {
    packets.sort_by_key(|p| p.raw_ts_us);
}

pub fn tolerance_order(packets: &mut [PacketMeta], window_us: u64) {
    packets.sort_by(|a, b| {
        let dt = if a.raw_ts_us > b.raw_ts_us {
            a.raw_ts_us - b.raw_ts_us
        } else {
            b.raw_ts_us - a.raw_ts_us
        };
        if dt <= window_us {
            a.index.cmp(&b.index)
        } else {
            a.raw_ts_us.cmp(&b.raw_ts_us).then_with(|| a.index.cmp(&b.index))
        }
    });
}
