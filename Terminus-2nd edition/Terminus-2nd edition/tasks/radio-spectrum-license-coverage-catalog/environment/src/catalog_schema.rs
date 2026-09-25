use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub wal_path: String,
    pub coverage_path: String,
    pub bundle_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BBox {
    pub lat_min: f64,
    pub lat_max: f64,
    pub lon_min: f64,
    pub lon_max: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BandSpec {
    pub band_id: String,
    pub mhz_low: f64,
    pub mhz_high: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LicenseGrant {
    pub license_id: String,
    pub holder: String,
    pub band_id: String,
    pub priority: u32,
    pub renewal_date: String,
    pub area: BBox,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransmitterSite {
    pub site_id: String,
    pub lat: f64,
    pub lon: f64,
    pub band_id: String,
    pub license_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExclusionZone {
    pub exclusion_id: String,
    pub band_id: String,
    pub area: BBox,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BundleFile {
    pub bundle_name: String,
    pub as_of_date: String,
    pub bands: Vec<BandSpec>,
    pub licenses: Vec<LicenseGrant>,
    pub transmitters: Vec<TransmitterSite>,
    pub exclusions: Vec<ExclusionZone>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalLicenseRow {
    pub license_id: String,
    pub holder: String,
    pub band_id: String,
    pub priority: u32,
    pub renewal_date: String,
    pub lat_min: f64,
    pub lat_max: f64,
    pub lon_min: f64,
    pub lon_max: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GrantWalFrame {
    pub load_generation: u64,
    pub seed: String,
    pub bundle: String,
    pub as_of_date: String,
    pub licenses: Vec<WalLicenseRow>,
    pub transmitters: Vec<TransmitterSite>,
    pub exclusions: Vec<ExclusionZone>,
    pub bands: Vec<BandSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageActive {
    pub seed: String,
    pub bundle: String,
    pub atlas_seq_id: String,
    pub load_generation: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageGeneration {
    pub active: Option<CoverageActive>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AtlasSiteRow {
    pub site_id: String,
    pub license_id: String,
    pub holder: String,
    pub band_id: String,
    pub effective_mhz_low: f64,
    pub effective_mhz_high: f64,
    pub excluded: bool,
    pub overlap_peer_count: u32,
    pub valid_through: String,
    pub atlas_seq_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AtlasSummary {
    pub total_sites: u32,
    pub active_sites: u32,
    pub excluded_sites: u32,
    pub overlap_pairs: u32,
    pub expired_dropped: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RfAtlasReport {
    pub seed: String,
    pub bundle: String,
    pub atlas_seq_id: String,
    pub catalog_rows: Vec<AtlasSiteRow>,
    pub summary: AtlasSummary,
    pub audit_digest: String,
}
