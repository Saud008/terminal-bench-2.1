use std::collections::HashSet;

use crate::depcrawl::adjacency::reachable_packages;
use crate::types::AtlasStage;

pub fn packages_for_binary(stage: &AtlasStage, _binary: &str, root: &str) -> HashSet<String> {
    reachable_packages(stage, root)
}

pub fn apply_salt(purl: &str) -> String {
    if let Ok(salt) = std::env::var("TB3_BUNDLE_SALT") {
        if !salt.is_empty() {
            return format!("{purl}{salt}");
        }
    }
    purl.to_string()
}
