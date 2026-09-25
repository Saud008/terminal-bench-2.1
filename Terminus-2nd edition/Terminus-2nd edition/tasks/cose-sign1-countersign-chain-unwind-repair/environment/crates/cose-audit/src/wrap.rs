use crate::model::CoseSign1;

pub fn rewrap_countersign_headers(sign1: &mut CoseSign1) {
    for cs in sign1.countersigns.iter_mut() {
        let mut keys: Vec<i64> = cs.protected.keys().copied().collect();
        keys.sort_unstable();
        let mut rebuilt = std::collections::BTreeMap::new();
        for k in keys {
            if let Some(v) = cs.protected.get(&k) {
                rebuilt.insert(k, v.clone());
            }
        }
        cs.protected = rebuilt;
    }
}
