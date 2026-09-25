use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize)]
pub struct Catalog {
    pub max_sprite_px: u32,
    pub base_padding: u32,
    pub padding_stride: u32,
    pub scale_mod: u32,
    pub atlas_width: u32,
    pub atlas_height: u32,
    pub scalable: Vec<String>,
    pub pack_sets: Vec<PackSet>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PackSet {
    pub name: String,
    pub sprites: Vec<SpriteRef>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct SpriteRef {
    pub glyph_id: String,
    pub frame: u32,
    pub file: String,
    pub rotate: bool,
}

#[derive(Debug, Clone)]
pub struct PreparedSprite {
    pub glyph_id: String,
    pub frame: u32,
    pub rotate: bool,
    pub content_w: u32,
    pub content_h: u32,
    pub padded_w: u32,
    pub padded_h: u32,
    pub pixels: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct PlacedSprite {
    pub glyph_id: String,
    pub frame: u32,
    pub atlas_x: u32,
    pub atlas_y: u32,
    pub content_w: u32,
    pub content_h: u32,
    pub rotate: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ManifestSprite {
    pub glyph_id: String,
    pub frame: u32,
    pub atlas_x: u32,
    pub atlas_y: u32,
    pub content_w: u32,
    pub content_h: u32,
    pub rotate: bool,
    pub u0: f64,
    pub v0: f64,
    pub u1: f64,
    pub v1: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Manifest {
    pub atlas_width: u32,
    pub atlas_height: u32,
    pub padding_px: u32,
    pub seed: u64,
    pub sprites: Vec<ManifestSprite>,
    pub checksum: String,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct ProbeResult {
    pub glyph_id: String,
    pub frame: u32,
    pub u: f64,
    pub v: f64,
    pub rgba: [u8; 4],
}

#[derive(Debug)]
pub enum AtlasError {
    Io(String),
    Parse(String),
    Oversized(String),
    Layout(String),
    NotFound(String),
}

impl std::fmt::Display for AtlasError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AtlasError::Io(m) => write!(f, "io: {m}"),
            AtlasError::Parse(m) => write!(f, "parse: {m}"),
            AtlasError::Oversized(m) => write!(f, "oversized: {m}"),
            AtlasError::Layout(m) => write!(f, "layout: {m}"),
            AtlasError::NotFound(m) => write!(f, "not found: {m}"),
        }
    }
}

impl std::error::Error for AtlasError {}

impl AtlasError {
    pub fn is_oversized(&self) -> bool {
        matches!(self, AtlasError::Oversized(_))
    }
}
