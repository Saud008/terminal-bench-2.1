use crate::model::Q16;

pub const Q16_ONE: Q16 = 65536;

pub fn q16_add(a: Q16, b: Q16) -> Q16 {
    a.saturating_add(b)
}

pub fn q16_from_units(units: i32) -> Q16 {
    units.saturating_mul(Q16_ONE)
}
