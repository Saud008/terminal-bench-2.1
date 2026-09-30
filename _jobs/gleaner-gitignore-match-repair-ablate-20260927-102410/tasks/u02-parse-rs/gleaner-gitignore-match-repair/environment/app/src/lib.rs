//! gleaner decides which files of a work tree git would treat as ignored,
//! without running git. See `docs/` for the exact rules it follows.

pub mod cli;
pub mod config;
pub mod error;
pub mod ignore;
pub mod report;
pub mod walk;
