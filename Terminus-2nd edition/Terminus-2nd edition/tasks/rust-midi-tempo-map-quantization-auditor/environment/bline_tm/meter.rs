use crate::types::TimeSig;

        pub fn ticks_per_beat(ppq: u32, meter: &TimeSig) -> u32 {
            ppq * meter.numerator
        }

pub fn active_meter(tick: u64, meters: &[TimeSig]) -> TimeSig {
    let mut active = meters[0].clone();
    for m in meters {
        if m.tick <= tick {
            active = m.clone();
        }
    }
    active
}
