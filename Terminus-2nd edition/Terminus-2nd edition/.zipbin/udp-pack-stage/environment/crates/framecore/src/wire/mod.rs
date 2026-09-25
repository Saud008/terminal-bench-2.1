pub mod loss_mask;
pub mod parser;
pub mod seq;

pub use loss_mask::{gaps_from_mask, decode_loss_mask};
pub use parser::parse_frame;
pub use seq::seq_before;
