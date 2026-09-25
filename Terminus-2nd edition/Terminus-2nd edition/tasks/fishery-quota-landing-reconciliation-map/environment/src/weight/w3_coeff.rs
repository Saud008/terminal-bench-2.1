pub fn live_kg_from_product(product_kg: f64, factor: f64) -> f64 {
    if factor <= 0.0 {
        return 0.0;
    }
    ((product_kg / factor) * 100.0).round() / 100.0
}
