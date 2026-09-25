pub fn tick_to_frame(tick: u32, tick_rate: u32, fps: u32) -> u32 {
    (tick * fps + tick_rate / 2) / tick_rate
}

pub fn tick_to_ms(tick: u32, tick_rate: u32) -> u64 {
    (tick as u64) * 1000 / tick_rate as u64
}
