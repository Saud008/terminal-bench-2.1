//! Pool weight table helpers — not on settlement or export hot path.

use crate::decoy;

pub fn blended_legendary_weight(common: u64, rare: u64, legendary: u64) -> u64 {
    decoy::blended_legendary_weight(common, rare, legendary)
}
