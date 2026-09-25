pub fn live_kg_from_product(product_kg: f64, factor: f64) -> f64 {
    ((product_kg * factor) * 100.0).round() / 100.0
}
