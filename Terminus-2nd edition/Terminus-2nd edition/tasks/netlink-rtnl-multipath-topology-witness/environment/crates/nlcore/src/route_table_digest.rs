use sha2::{Digest, Sha256};

use crate::model::RouteOut;

/// Legacy route-table digest helper (not used by nlctl decode).
pub fn route_table_digest(seed: &str, routes: &[RouteOut]) -> String {
    let mut parts = vec![seed.to_string(), routes.len().to_string()];
    for route in routes {
        parts.push(route.table.to_string());
    }
    format!("{:x}", Sha256::digest(parts.join("\n").as_bytes()))
}
