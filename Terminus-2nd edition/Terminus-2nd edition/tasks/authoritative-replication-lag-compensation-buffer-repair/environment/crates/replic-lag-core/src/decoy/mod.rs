//! Decoy surface that must not influence production lag or snapshot paths.

pub mod wrap;

pub use wrap::{blend_rtt_us, decoy_integrity};
