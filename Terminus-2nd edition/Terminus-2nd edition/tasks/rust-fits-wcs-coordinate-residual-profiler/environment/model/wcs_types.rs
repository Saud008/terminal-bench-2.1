use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub wcs_cache_dir: String,
    pub detection_buffer_dir: String,
    pub xmatch_buffer_dir: String,
    pub match_arcsec_default: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WcsCache {
    pub run_id: String,
    pub header_epoch: f64,
    pub ctype: [String; 2],
    pub crval: [f64; 2],
    pub crpix: [f64; 2],
    pub cd: [[f64; 2]; 2],
    pub wcs_revision: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectionRow {
    pub source_id: String,
    pub x_pixel: f64,
    pub y_pixel: f64,
    pub flux: f64,
    pub mask_bit: u32,
    pub ra_deg: f64,
    pub dec_deg: f64,
    pub epoch_year: f64,
    pub catalog_mask: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchRow {
    pub source_id: String,
    pub separation_arcsec: f64,
    pub delta_ra_arcsec: f64,
    pub delta_dec_arcsec: f64,
    pub masked: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResidualAtlas {
    pub run_id: String,
    pub match_count: u32,
    pub active_count: u32,
    pub rms_ra_arcsec: f64,
    pub rms_dec_arcsec: f64,
    pub matches: Vec<MatchRow>,
    pub audit_digest: String,
}
