use std::collections::BTreeMap;

pub fn average_holdings(tonnage: &BTreeMap<String, f64>) -> f64 {
    if tonnage.is_empty() {
        return 0.0;
    }
    tonnage.values().sum::<f64>() / tonnage.len() as f64
}
