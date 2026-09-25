pub mod patch;
pub mod zlib;

pub use patch::apply_patch;
pub use zlib::{inflate_at, inflate_fresh};
