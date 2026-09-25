//! fbpkg — FlatBuffers scene decode / staging / JSON export.

pub mod bd13;
pub mod cv20;
pub mod fk65;
pub mod ft26;
pub mod gp94;
pub mod hn55;
pub mod je67;
pub mod kx42;
pub mod mp93;
pub mod qg71;
pub mod rw14;
pub mod st38;
pub mod ul82;
pub mod wrap;
pub mod yl49;
pub mod zq81;

// Semantic aliases used by the module graph (same sources, alternate paths).
#[path = "cv20.rs"]
pub mod kx42_snapshot;

#[path = "hn55.rs"]
pub mod kx42_digest;

#[path = "je67.rs"]
pub mod export;

#[path = "qg71.rs"]
pub mod stdout_render;

#[path = "zq81.rs"]
pub mod guard;

#[path = "yl49.rs"]
pub mod scene_seal;

#[path = "yl49.rs"]
pub mod mp93_digest;

#[path = "je67.rs"]
pub mod je67_stage;
