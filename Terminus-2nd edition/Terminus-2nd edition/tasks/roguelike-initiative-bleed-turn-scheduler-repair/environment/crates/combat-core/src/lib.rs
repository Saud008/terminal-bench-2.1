pub mod bleed;
pub mod error;
pub mod export;
pub mod ingest;
pub mod model;
pub mod scheduler;
pub mod simulate;

pub use error::{CombatError, Result};
pub use export::export_transcript;
pub use ingest::ingest_roster;
pub use simulate::{read_state, simulate_combat, write_state};
