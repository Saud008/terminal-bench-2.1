use crate::model::Catalog;

pub fn padding_px(catalog: &Catalog, seed: u64) -> u32 {
    catalog.base_padding + (seed as u32 % catalog.padding_stride)
}

pub fn scale_factor(catalog: &Catalog, seed: u64) -> u32 {
    1 + (seed as u32 % catalog.scale_mod)
}

pub fn scaled_dim(base: u32, scale: u32) -> u32 {
    std::cmp::max(1, base.saturating_mul(scale))
}
