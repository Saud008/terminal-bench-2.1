//! Ignore rules: reading pattern files, matching paths, and combining the
//! per-directory, repository and user sources.

mod charclass;
mod lines;
mod parse;
mod pattern;
mod sources;
mod stack;
mod wildmatch;

pub use pattern::{Pattern, PatternList};
pub use sources::Sources;
pub use stack::{inherit, resolve, Hit, Matcher, Verdict};
pub use wildmatch::wildmatch;
